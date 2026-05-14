# Inbox Reader + Tool Audit Design

**Date:** 2026-05-14
**Status:** Approved

## Goal

Add email reading/search capabilities (list, get, mark read/unread) to the Gmail MCP server, and remove static guidance content (tools, prompts, resources) that the LLM already handles natively. Remove `send_email` in favor of a draft-review-send safety workflow.

## Audit: What stays, what goes

### Removed (12 items)

| Type | Name | Reason |
|------|------|--------|
| Tool | `send_email` | No draft-review safety net; irreversible. Prefer create_draft -> human review -> send_draft |
| Tool | `get_subject_line_help` | Static content; LLM does better |
| Tool | `validate_subject_line_tool` | Static content; LLM does better |
| Tool | `get_email_templates` | Static content; LLM does better |
| Prompt | `professional_email_composer` | Hardcoded template; no unique capability |
| Prompt | `follow_up_email_generator` | Hardcoded template; no unique capability |
| Prompt | `meeting_request_composer` | Hardcoded template; no unique capability |
| Prompt | `draft_strategy_advisor` | Hardcoded template; no unique capability |
| Prompt | `email_review_checklist` | Hardcoded template; no unique capability |
| Resource | `template://html_email/{name}` | Static templates; LLM composes better |
| Resource | `template://signature/{type}` | Static templates; LLM composes better |
| Resource | `guidelines://security/{category}` | Static content; LLM knows this |
| Resource | `guidelines://etiquette/{category}` | Static content; LLM knows this |

Deleted files: `src/guidance/` tree, `src/resources/` tree, `tests/test_guidance.py`

### Kept (4 operational tools)

| Tool | Reason |
|------|--------|
| `create_draft` | Core: AI composes draft, human reviews |
| `send_draft` | Core: human-reviewed send |
| `list_drafts` | Core: browse pending drafts |
| `get_user_info` | Connectivity smoke test |

### Added (1 + 4 = 5 tools)

| Tool | Reason |
|------|--------|
| `delete_draft` | Expose existing gateway capability to clean up discarded drafts |
| `list_emails` | Search/list inbox with Gmail query syntax, labels, pagination |
| `get_email` | Fetch full email content (headers, body, attachments) by ID |
| `mark_as_read` | Remove UNREAD label from a message |
| `mark_as_unread` | Add UNREAD label to a message |

## Final tool set (9 tools)

1. `create_draft` — compose and save draft
2. `send_draft` — send existing draft
3. `list_drafts` — browse drafts
4. `delete_draft` — discard a draft
5. `list_emails` — search inbox with filters
6. `get_email` — fetch full email content
7. `mark_as_read` — mark message read
8. `mark_as_unread` — mark message unread
9. `get_user_info` — connectivity smoke test

## New tool signatures

### `list_emails`

```
query: str = ""              — Gmail search syntax (e.g., "is:unread", "from:alice@example.com")
label_ids: list[str] = []    — Gmail label IDs to filter by
max_results: int = 20        — Max results per page
include_spam_trash: bool = False  — Whether to include SPAM and TRASH
page_token: str = ""         — Token for next page
```

Returns `List[EmailListItem]` with: id, thread_id, label_ids, snippet, subject, from, to, date, internal_date

### `get_email`

```
email_id: str  — Message ID
```

Returns `EmailDetail` with: id, thread_id, label_ids, snippet, subject, from, to, cc, bcc, date, internal_date, body_text, body_html, attachments (filename + mime_type)

### `mark_as_read` / `mark_as_unread`

```
email_id: str  — Message ID
```

Returns `bool` on success.

## Models

```python
class EmailListItem(BaseModel):
    id: str
    thread_id: str
    label_ids: list[str]
    snippet: str
    subject: str
    from_: str = Field(alias="from")
    to: str
    date: str
    internal_date: str

class EmailAddress(BaseModel):
    name: str = ""
    email: str

class AttachmentInfo(BaseModel):
    filename: str
    mime_type: str

class EmailDetail(BaseModel):
    id: str
    thread_id: str
    label_ids: list[str]
    snippet: str
    subject: str
    from_: EmailAddress
    to: list[EmailAddress]
    cc: list[EmailAddress]
    bcc: list[EmailAddress]
    date: str
    internal_date: str
    body_text: str
    body_html: str
    attachments: list[AttachmentInfo]
```

## Gateway additions

Three new methods on `GmailGateway`:

- `list_messages(query, label_ids, max_results, include_spam_trash, page_token)` — calls `users().messages().list()`, parses headers for each message
- `get_message(email_id)` — calls `users().messages().get(format="full")`, extracts headers, body text+html, attachment metadata
- `modify_labels(email_id, add_label_ids, remove_label_ids)` — calls `users().messages().modify()`, used by mark_as_read/unread

## Architecture notes

- No new dependencies required — all Gmail API calls already available via `google-api-python-client`
- Session pattern unchanged: `gateway -> session -> MCP tool`
- Flat single-purpose tools (same pattern as existing draft tools)
- `mark_as_read` removes `UNREAD` label; `mark_as_unread` adds `UNREAD` label — no toggle, explicit intent
