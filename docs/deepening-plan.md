# Deepening Plan

This plan continues the FastMCP rewrite after the initial **Gmail Token Store** and **Gmail Session** split. It assumes the local stdio server model recorded in [`CONTEXT.md`](../CONTEXT.md) and ADR-0001.

## 1. Mail Composition

**Goal**: isolate MIME/message construction from Gmail API calls.

**Current friction**: `send_email` and `create_draft` duplicate recipient/header/body/raw-message creation inside `GmailClient`.

**Proposed module**: `src/mail_composer.py`

**Interface**:

```python
class MailComposer:
    def compose(self, request: EmailRequest, sender: str) -> RawMessage: ...
```

**Test-first steps**:

- plain-text email sets `To`, `Subject`, `From`, body.
- HTML email creates multipart alternative with text and HTML parts.
- optional `Cc`/`Bcc` are omitted when absent and present when supplied.
- encoded raw payload decodes to a valid `EmailMessage`.

**File changes**:

- add `src/mail_composer.py`
- update `src/gmail_client.py` to call composer
- consider replacing duplicate `DraftRequest` with `EmailRequest`
- add `tests/test_mail_composer.py`

**Acceptance criteria**:

- no MIME/header construction remains duplicated in send/draft paths.
- Gmail API tests do not need to parse MIME details.
- composer tests run without Google dependencies.

## 2. Gmail Gateway

**Goal**: isolate Google API chain calls and error translation.

**Current friction**: `GmailClient` mixes Gmail profile lookup, message composition, Google discovery client chains, and response shaping.

**Proposed module**: `src/gmail_gateway.py`

**Interface**:

```python
class GmailGateway:
    def get_profile(self) -> UserInfo: ...
    def send_raw_message(self, raw: str) -> EmailResponse: ...
    def create_raw_draft(self, raw: str) -> EmailResponse: ...
    def send_draft(self, draft_id: str) -> EmailResponse: ...
    def list_drafts(self, max_results: int) -> list[DraftInfo]: ...
```

**Test-first steps**:

- fake Google service returns mapped `EmailResponse`.
- draft listing maps headers/snippets correctly.
- `HttpError` becomes a project-level Gmail error.

**File changes**:

- add `src/gmail_gateway.py`
- move Google `build("gmail", "v1", ...)` adapter logic there
- make `GmailSession` coordinate gateway and composer
- shrink or delete `src/gmail_client.py`
- add `tests/test_gmail_gateway.py`

**Acceptance criteria**:

- only gateway knows Google discovery chain shape.
- session tests can use a fake gateway.
- tool handlers never import Google SDK types.

## 3. Server Assembly

**Goal**: remove import-time globals as the main server seam.

**Current friction**: `src/server.py` creates global `mcp`, token store, and session factory at import time; tests must work around real `~/.gmail-mcp`.

**Proposed module shape**:

```python
def create_server(session_factory: GmailSessionFactory) -> FastMCP: ...
def create_default_server() -> FastMCP: ...
```

**Test-first steps**:

- create server with fake session factory.
- call registered operational tool directly if FastMCP exposes callable metadata, or test wrapper functions before registration.
- missing session returns the expected authentication-required error.

**File changes**:

- update `src/server.py` to expose factory functions
- move global construction to `create_default_server`
- update `main.py` to call `create_default_server()`
- preserve compatibility export `mcp = create_default_server()` only if needed
- add `tests/test_server_tools.py`

**Acceptance criteria**:

- importing `src.server` does not create or touch `~/.gmail-mcp`.
- CLI remains fail-fast when no Current Gmail User exists.
- tests can build server with fake Gmail Session.

## 4. Guidance Content

**Goal**: separate email-writing guidance from Gmail operations.

**Current friction**: large prompt strings and resource registrations dominate `server.py`, making operational behavior hard to scan.

**Proposed modules**:

- `src/guidance/prompts.py`
- `src/guidance/resources.py`
- optionally `src/guidance/tools.py` for subject/template helper tools.

**Interface**:

```python
def register_guidance_prompts(mcp: FastMCP) -> None: ...
def register_guidance_resources(mcp: FastMCP) -> None: ...
def register_guidance_tools(mcp: FastMCP) -> None: ...
```

**Test-first steps**:

- prompt functions return expected key sections for representative inputs.
- resource functions return known templates/guidelines.
- invalid resource names raise clear `ValueError`.

**File changes**:

- add `src/guidance/__init__.py`
- move prompt/resource/tool registration out of `src/server.py`
- keep existing `src/resources/*` as content data modules
- add `tests/test_guidance.py`

**Acceptance criteria**:

- `server.py` mostly wires modules and defines Gmail operation tools.
- guidance tests do not import token store or Google SDK.
- resources/prompts remain behavior-compatible for MCP clients.

## Suggested Order

1. Mail Composition
2. Gmail Gateway
3. Server Assembly
4. Guidance Content

This order builds depth from pure logic toward FastMCP wiring.
