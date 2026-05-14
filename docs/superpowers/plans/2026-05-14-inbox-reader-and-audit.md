# Inbox Reader + Tool Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email reading/search tools (list, get, mark read/unread), expose delete_draft, remove send_email, and delete all static guidance content (tools, prompts, resources).

**Architecture:** Same flat-tool pattern as existing draft tools. Gateway methods -> Session wrappers -> MCP tools. New models for email list/detail responses. No new dependencies.

**Tech Stack:** Python 3.12, FastMCP, google-api-python-client, Pydantic

**Branch:** `feat/inbox-reader-and-audit`

---

### Task 1: Add email-reading models to src/models.py

**Files:**
- Modify: `src/models.py`

- [ ] **Step 1: Add EmailAddress model**

```python
"""Pydantic models for Gmail MCP server."""

from typing import Optional, List
from pydantic import BaseModel, Field


class EmailAddress(BaseModel):
    """Email address with optional display name."""

    name: str = ""
    email: str


class EmailRequest(BaseModel):
    """Request model for sending an email."""

    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    html_body: Optional[str] = None


class EmailResponse(BaseModel):
    """Response model for email operations."""

    id: str
    thread_id: str
    status: str
    message: Optional[str] = None


class DraftInfo(BaseModel):
    """Draft information model."""

    id: str
    message_id: str
    thread_id: str
    subject: str
    to: str
    snippet: str


class UserInfo(BaseModel):
    """User profile information model."""

    email: str
    messages_total: int
    threads_total: int


class AttachmentInfo(BaseModel):
    """Email attachment metadata."""

    filename: str
    mime_type: str


class EmailListItem(BaseModel):
    """Summary info for one message in a listing."""

    id: str
    thread_id: str
    label_ids: List[str]
    snippet: str
    subject: str
    from_: str = Field(alias="from")
    to: str
    date: str
    internal_date: str


class EmailDetail(BaseModel):
    """Full content of a single email message."""

    id: str
    thread_id: str
    label_ids: List[str]
    snippet: str
    subject: str
    from_: EmailAddress = Field(alias="from")
    to: List[EmailAddress]
    cc: List[EmailAddress]
    bcc: List[EmailAddress]
    date: str
    internal_date: str
    body_text: str
    body_html: str
    attachments: List[AttachmentInfo]
```

- [ ] **Step 2: Verify models import correctly**

Run: `uv run python -c "from src.models import EmailListItem, EmailDetail, EmailAddress, AttachmentInfo; print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add src/models.py
git commit -m "feat: add email-reader models (EmailListItem, EmailDetail, EmailAddress, AttachmentInfo)"
```

---

### Task 2: Add gateway methods to src/gmail_gateway.py

**Files:**
- Modify: `src/gmail_gateway.py`

- [ ] **Step 1: Write the failing test**

The `list_messages` method parses headers from a `messages().list()` response and returns `List[EmailListItem]`. The `get_message` method returns a full `EmailDetail`. The `modify_labels` method adds/removes labels on a message.

Create test file `tests/test_gmail_gateway.py` if it doesn't already have a section for these. Add these test classes after the existing `TestDeleteDraft` class:

```python
class TestListMessages:
    def test_returns_email_list_items(self, gateway, mock_service):
        mock_service.users().messages().list.return_value.execute.return_value = {
            "messages": [
                {"id": "msg1", "threadId": "t1"},
                {"id": "msg2", "threadId": "t2"},
            ],
            "nextPageToken": "tok",
            "resultSizeEstimate": 2,
        }
        get_returns = [
            {
                "id": "msg1",
                "threadId": "t1",
                "labelIds": ["INBOX", "UNREAD"],
                "snippet": "Hello world",
                "internalDate": "1715700000000",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test"},
                        {"name": "From", "value": "alice@example.com"},
                        {"name": "To", "value": "bob@example.com"},
                        {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                    ]
                },
            },
            {
                "id": "msg2",
                "threadId": "t2",
                "labelIds": ["INBOX"],
                "snippet": "Another",
                "internalDate": "1715700000001",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Re: Test"},
                        {"name": "From", "value": "bob@example.com"},
                        {"name": "To", "value": "alice@example.com"},
                        {"name": "Date", "value": "Tue, 14 May 2026 11:00:00 +0000"},
                    ]
                },
            },
        ]
        mock_service.users().messages().get.return_value.execute.side_effect = get_returns

        result = gateway.list_messages(query="is:unread", max_results=10)

        mock_service.users().messages().list.assert_called_once_with(
            userId="me", q="is:unread", maxResults=10, pageToken=None,
            includeSpamTrash=False,
        )
        assert len(result) == 2
        assert result[0].id == "msg1"
        assert result[0].subject == "Test"
        assert result[0].from_ == "alice@example.com"
        assert result[0].snippet == "Hello world"
        assert "UNREAD" in result[0].label_ids

    def test_handles_empty_results(self, gateway, mock_service):
        mock_service.users().messages().list.return_value.execute.return_value = {}

        result = gateway.list_messages()

        assert result == []

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().list().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to list messages"):
            gateway.list_messages()


class TestGetMessage:
    def test_returns_email_detail(self, gateway, mock_service):
        mock_service.users().messages().get.return_value.execute.return_value = {
            "id": "msg1",
            "threadId": "t1",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Hello world",
            "internalDate": "1715700000000",
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "From", "value": "Alice <alice@example.com>"},
                    {"name": "To", "value": "Bob <bob@example.com>"},
                    {"name": "Cc", "value": "Carol <carol@example.com>"},
                    {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                ],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                    {"mimeType": "text/html", "body": {"data": "PGgxPkhlbGxvPC9oMT4="}},
                    {
                        "mimeType": "application/pdf",
                        "filename": "report.pdf",
                        "body": {"attachmentId": "att1"},
                    },
                ],
            },
        }

        result = gateway.get_message("msg1")

        assert result.id == "msg1"
        assert result.subject == "Test Email"
        assert result.from_.email == "alice@example.com"
        assert result.from_.name == "Alice"
        assert result.to[0].email == "bob@example.com"
        assert result.to[0].name == "Bob"
        assert result.cc[0].email == "carol@example.com"
        assert result.body_text == "Hello"
        assert result.body_html == "<h1>Hello</h1>"
        assert result.attachments[0].filename == "report.pdf"
        assert result.attachments[0].mime_type == "application/pdf"

    def test_handles_simple_text_body(self, gateway, mock_service):
        mock_service.users().messages().get.return_value.execute.return_value = {
            "id": "msg1",
            "threadId": "t1",
            "labelIds": ["INBOX"],
            "snippet": "Hi",
            "internalDate": "1715700000000",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Hi"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "To", "value": "bob@example.com"},
                    {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                ],
                "body": {"data": "SGk="},
            },
        }

        result = gateway.get_message("msg1")

        assert result.body_text == "Hi"
        assert result.body_html == ""
        assert result.attachments == []

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().get().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to get message"):
            gateway.get_message("msg1")


class TestModifyLabels:
    def test_modifies_labels(self, gateway, mock_service):
        mock_service.users().messages().modify.return_value.execute.return_value = {
            "id": "msg1",
            "labelIds": ["INBOX"],
        }

        result = gateway.modify_labels(
            "msg1", add_label_ids=["STARRED"], remove_label_ids=["UNREAD"]
        )

        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": ["STARRED"], "removeLabelIds": ["UNREAD"]},
        )

    def test_handles_remove_only(self, gateway, mock_service):
        mock_service.users().messages().modify.return_value.execute.return_value = {
            "id": "msg1",
            "labelIds": [],
        }

        result = gateway.modify_labels("msg1", remove_label_ids=["UNREAD"])

        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": [], "removeLabelIds": ["UNREAD"]},
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().modify().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to modify labels"):
            gateway.modify_labels("msg1", add_label_ids=["STARRED"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gmail_gateway.py::TestListMessages tests/test_gmail_gateway.py::TestGetMessage tests/test_gmail_gateway.py::TestModifyLabels -v`
Expected: FAIL with "AttributeError: 'GmailGateway' object has no attribute 'list_messages'"

- [ ] **Step 3: Implement gateway methods in src/gmail_gateway.py**

Add these methods to `GmailGateway` class (after `delete_draft` at line 142):

```python
    def list_messages(
        self,
        query: str = "",
        label_ids: list[str] | None = None,
        max_results: int = 20,
        include_spam_trash: bool = False,
        page_token: str | None = None,
    ) -> List["EmailListItem"]:
        """List messages matching query and label filters.

        Uses Gmail's native search syntax for the query parameter.
        """
        from .models import EmailListItem

        try:
            kwargs: dict = {
                "userId": "me",
                "q": query,
                "maxResults": max_results,
                "includeSpamTrash": include_spam_trash,
            }
            if label_ids:
                kwargs["labelIds"] = label_ids
            if page_token:
                kwargs["pageToken"] = page_token

            results = (
                self._service.users().messages().list(**kwargs).execute()
            )

            messages = results.get("messages", [])
            items: List[EmailListItem] = []

            for msg in messages:
                detail = (
                    self._service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="metadata",
                         metadataHeaders=["Subject", "From", "To", "Date"])
                    .execute()
                )

                headers = detail.get("payload", {}).get("headers", [])
                header_map = {h["name"]: h["value"] for h in headers}

                items.append(
                    EmailListItem(
                        id=detail["id"],
                        thread_id=detail["threadId"],
                        label_ids=detail.get("labelIds", []),
                        snippet=detail.get("snippet", ""),
                        subject=header_map.get("Subject", "No Subject"),
                        from_=header_map.get("From", "Unknown"),
                        to=header_map.get("To", ""),
                        date=header_map.get("Date", ""),
                        internal_date=detail.get("internalDate", ""),
                    )
                )

            return items

        except HttpError as e:
            raise GmailError(f"Failed to list messages: {e}")

    def get_message(self, email_id: str) -> "EmailDetail":
        """Get full message content by ID."""
        from .models import EmailDetail, EmailAddress, AttachmentInfo

        try:
            detail = (
                self._service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            headers = detail.get("payload", {}).get("headers", [])
            header_map = {h["name"]: h["value"] for h in headers}

            body_text, body_html, attachments = self._parse_parts(
                detail.get("payload", {})
            )

            return EmailDetail(
                id=detail["id"],
                thread_id=detail["threadId"],
                label_ids=detail.get("labelIds", []),
                snippet=detail.get("snippet", ""),
                subject=header_map.get("Subject", "No Subject"),
                from_=self._parse_email_address(header_map.get("From", "")),
                to=self._parse_email_addresses(header_map.get("To", "")),
                cc=self._parse_email_addresses(header_map.get("Cc", "")),
                bcc=self._parse_email_addresses(header_map.get("Bcc", "")),
                date=header_map.get("Date", ""),
                internal_date=detail.get("internalDate", ""),
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
            )

        except HttpError as e:
            raise GmailError(f"Failed to get message: {e}")

    def modify_labels(
        self,
        email_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> bool:
        """Add or remove labels on a message."""
        try:
            self._service.users().messages().modify(
                userId="me",
                id=email_id,
                body={
                    "addLabelIds": add_label_ids or [],
                    "removeLabelIds": remove_label_ids or [],
                },
            ).execute()
            return True
        except HttpError as e:
            raise GmailError(f"Failed to modify labels: {e}")

    @staticmethod
    def _parse_email_address(header_value: str) -> "EmailAddress":
        """Parse a single email address header value (e.g. 'Alice <alice@example.com>')."""
        from .models import EmailAddress
        import re
        match = re.match(r"(.+?)\s*<(.+?)>", header_value)
        if match:
            return EmailAddress(name=match.group(1).strip(), email=match.group(2).strip())
        return EmailAddress(email=header_value.strip())

    @staticmethod
    def _parse_email_addresses(header_value: str) -> list:
        """Parse multiple email addresses from a header value."""
        from .models import EmailAddress
        if not header_value:
            return []
        import re
        addresses = []
        for part in re.split(r",\s*(?=[^<]*<|[^,]+@)", header_value):
            part = part.strip()
            if part:
                match = re.match(r"(.+?)\s*<(.+?)>", part)
                if match:
                    addresses.append(EmailAddress(name=match.group(1).strip(), email=match.group(2).strip()))
                else:
                    addresses.append(EmailAddress(email=part))
        return addresses

    @staticmethod
    def _parse_parts(payload: dict) -> tuple:
        """Extract text body, html body, and attachment list from message payload.

        Returns (body_text: str, body_html: str, attachments: list[AttachmentInfo])
        """
        from .models import AttachmentInfo
        import base64

        body_text = ""
        body_html = ""
        attachments: list = []

        parts = payload.get("parts", [])

        if payload.get("mimeType") == "text/plain" and not parts:
            data = payload.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
            return body_text, body_html, attachments

        if payload.get("mimeType") == "text/html" and not parts:
            data = payload.get("body", {}).get("data", "")
            if data:
                body_html = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
            return body_text, body_html, attachments

        for part in parts:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
            elif mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_html = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
            elif part.get("filename") and part.get("body", {}).get("attachmentId"):
                attachments.append(
                    AttachmentInfo(
                        filename=part["filename"],
                        mime_type=mime_type,
                    )
                )
            elif "parts" in part:
                sub_text, sub_html, sub_att = GmailGateway._parse_parts(part)
                if sub_text:
                    body_text = sub_text
                if sub_html:
                    body_html = sub_html
                attachments.extend(sub_att)

        return body_text, body_html, attachments
```

Also update the import at the top to include `List` (it's already imported from typing):
```python
from typing import List
```
(This import already exists, verify it.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_gmail_gateway.py -v`
Expected: ALL PASS (including existing tests)

- [ ] **Step 5: Commit**

```bash
git add src/gmail_gateway.py tests/test_gmail_gateway.py
git commit -m "feat: add list_messages, get_message, modify_labels to GmailGateway"
```

---

### Task 3: Add session wrappers in src/gmail_session.py

**Files:**
- Modify: `src/gmail_session.py`

- [ ] **Step 1: Add session methods**

```python
"""Gmail operation session for the selected local Gmail user."""

from typing import Protocol, List, Optional

from google.oauth2.credentials import Credentials

from .gmail_gateway import GmailGateway
from .mail_composer import MailComposer
from .models import EmailRequest, EmailListItem, EmailDetail


class GmailSession:
    """Ready-to-use Gmail operations for one current Gmail user."""

    def __init__(self, gateway: GmailGateway, composer: MailComposer):
        self._gateway = gateway
        self._composer = composer

    def get_user_info(self):
        return self._gateway.get_profile().model_dump()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        html_body: str | None = None,
    ):
        request = EmailRequest(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
        )
        sender = self._gateway.get_profile().email
        raw = self._composer.compose(request, sender)
        return self._gateway.send_raw_message(raw).model_dump()

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        html_body: str | None = None,
    ):
        request = EmailRequest(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
        )
        sender = self._gateway.get_profile().email
        raw = self._composer.compose(request, sender)
        return self._gateway.create_raw_draft(raw).model_dump()

    def send_draft(self, draft_id: str):
        return self._gateway.send_draft(draft_id).model_dump()

    def list_drafts(self, max_results: int = 10):
        drafts = self._gateway.list_drafts(max_results)
        return [d.model_dump() for d in drafts]

    def delete_draft(self, draft_id: str) -> bool:
        return self._gateway.delete_draft(draft_id)

    def list_emails(
        self,
        query: str = "",
        label_ids: Optional[List[str]] = None,
        max_results: int = 20,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
    ):
        items = self._gateway.list_messages(
            query=query,
            label_ids=label_ids,
            max_results=max_results,
            include_spam_trash=include_spam_trash,
            page_token=page_token,
        )
        return [item.model_dump() for item in items]

    def get_email(self, email_id: str):
        return self._gateway.get_message(email_id).model_dump()

    def mark_as_read(self, email_id: str) -> bool:
        return self._gateway.modify_labels(
            email_id, remove_label_ids=["UNREAD"]
        )

    def mark_as_unread(self, email_id: str) -> bool:
        return self._gateway.modify_labels(
            email_id, add_label_ids=["UNREAD"]
        )
```

The rest of the file (session factories) remains unchanged.

- [ ] **Step 2: Run tests to verify session layer works**

Run: `pytest tests/test_gmail_gateway.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add src/gmail_session.py
git commit -m "feat: add list_emails, get_email, mark_as_read/unread to GmailSession"
```

---

### Task 4: Update server.py — new tools, remove send_email, remove guidance

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Rewrite src/server.py**

```python
"""MCP server implementation for Gmail functionality."""

from typing import Optional, List
from fastmcp import FastMCP

from .gmail_session import CurrentGmailSessionFactory, GmailSession
from .models import (
    EmailRequest,
    EmailResponse,
    DraftInfo,
    UserInfo,
    EmailListItem,
    EmailDetail,
)

# Module-level session factory set by create_server()
_session_factory: CurrentGmailSessionFactory | None = None

# Dummy MCP instance used only for decorators (no runtime use)
_mcp = FastMCP("_internal")


def get_authenticated_session() -> Optional[GmailSession]:
    """Get authenticated Gmail session for current user."""
    if _session_factory is None:
        return None
    return _session_factory.create_current_session()


# Operational tools


@_mcp.tool()
async def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html_body: Optional[str] = None,
    ctx=None,
) -> EmailResponse:
    """Create an email draft.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        html_body: HTML version of email body (optional)
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Creating draft for {to}")

    try:
        draft_req = EmailRequest(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
        )

        result = session.create_draft(
            to=draft_req.to,
            subject=draft_req.subject,
            body=draft_req.body,
            cc=draft_req.cc,
            bcc=draft_req.bcc,
            html_body=draft_req.html_body,
        )

        if ctx:
            await ctx.info(f"Draft created with ID: {result['id']}")

        return EmailResponse(**result)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to create draft: {str(e)}")
        raise Exception(f"Failed to create draft: {str(e)}")


@_mcp.tool()
async def send_draft(draft_id: str, ctx=None) -> EmailResponse:
    """Send an existing email draft.

    Args:
        draft_id: ID of the draft to send
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Sending draft {draft_id}")

    try:
        result = session.send_draft(draft_id)

        if ctx:
            await ctx.info(f"Draft sent with message ID: {result['id']}")

        return EmailResponse(**result)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to send draft: {str(e)}")
        raise Exception(f"Failed to send draft: {str(e)}")


@_mcp.tool()
async def list_drafts(max_results: int = 10, ctx=None) -> List[DraftInfo]:
    """List email drafts.

    Args:
        max_results: Maximum number of drafts to return (default: 10)
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Listing up to {max_results} drafts")

    try:
        drafts = session.list_drafts(max_results)
        result = [DraftInfo(**draft) for draft in drafts]

        if ctx:
            await ctx.info(f"Found {len(result)} drafts")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list drafts: {str(e)}")
        raise Exception(f"Failed to list drafts: {str(e)}")


@_mcp.tool()
async def delete_draft(draft_id: str, ctx=None) -> bool:
    """Delete an email draft.

    Args:
        draft_id: ID of the draft to delete
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Deleting draft {draft_id}")

    try:
        result = session.delete_draft(draft_id)

        if ctx:
            await ctx.info(f"Draft {draft_id} deleted")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to delete draft: {str(e)}")
        raise Exception(f"Failed to delete draft: {str(e)}")


@_mcp.tool()
async def get_user_info(ctx=None) -> UserInfo:
    """Get current authenticated user information."""
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    try:
        user_info = session.get_user_info()
        result = UserInfo(**user_info)

        if ctx:
            await ctx.info(f"Current user: {result.email}")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get user info: {str(e)}")
        raise Exception(f"Failed to get user info: {str(e)}")


@_mcp.tool()
async def list_emails(
    query: str = "",
    label_ids: Optional[List[str]] = None,
    max_results: int = 20,
    include_spam_trash: bool = False,
    page_token: Optional[str] = None,
    ctx=None,
) -> List[EmailListItem]:
    """List emails from the inbox with optional filtering.

    Args:
        query: Gmail search query (e.g. "is:unread", "from:alice@example.com",
               "newer_than:2d", "subject:report"). Uses Gmail's native search syntax.
        label_ids: List of Gmail label IDs to filter by (e.g. ["INBOX", "IMPORTANT"])
        max_results: Maximum number of emails to return (default: 20)
        include_spam_trash: Whether to include emails from SPAM and TRASH
        page_token: Token for retrieving the next page of results
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Listing emails with query: '{query}'")

    try:
        emails = session.list_emails(
            query=query,
            label_ids=label_ids,
            max_results=max_results,
            include_spam_trash=include_spam_trash,
            page_token=page_token,
        )
        result = [EmailListItem(**email) for email in emails]

        if ctx:
            await ctx.info(f"Found {len(result)} emails")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list emails: {str(e)}")
        raise Exception(f"Failed to list emails: {str(e)}")


@_mcp.tool()
async def get_email(email_id: str, ctx=None) -> EmailDetail:
    """Get the full content of a specific email by ID.

    Args:
        email_id: The Gmail message ID of the email to retrieve
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Fetching email {email_id}")

    try:
        detail = session.get_email(email_id)
        result = EmailDetail(**detail)

        if ctx:
            await ctx.info(f"Retrieved email: {result.subject}")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get email: {str(e)}")
        raise Exception(f"Failed to get email: {str(e)}")


@_mcp.tool()
async def mark_as_read(email_id: str, ctx=None) -> bool:
    """Mark an email as read (removes UNREAD label).

    Args:
        email_id: The Gmail message ID to mark as read
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Marking email {email_id} as read")

    try:
        result = session.mark_as_read(email_id)

        if ctx:
            await ctx.info(f"Marked {email_id} as read")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to mark as read: {str(e)}")
        raise Exception(f"Failed to mark as read: {str(e)}")


@_mcp.tool()
async def mark_as_unread(email_id: str, ctx=None) -> bool:
    """Mark an email as unread (adds UNREAD label).

    Args:
        email_id: The Gmail message ID to mark as unread
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authorized Google user. Connect through Google OAuth first."
        )

    if ctx:
        await ctx.info(f"Marking email {email_id} as unread")

    try:
        result = session.mark_as_unread(email_id)

        if ctx:
            await ctx.info(f"Marked {email_id} as unread")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to mark as unread: {str(e)}")
        raise Exception(f"Failed to mark as unread: {str(e)}")


# Server assembly


def create_server(
    session_factory: CurrentGmailSessionFactory, *, auth=None
) -> FastMCP:
    """Create an MCP server wired to the given session factory.

    Importing this module does NOT touch the filesystem.
    """
    global _session_factory
    _session_factory = session_factory

    mcp = FastMCP("Gmail MCP Server", auth=auth)

    # Operational tools
    mcp.add_tool(create_draft)
    mcp.add_tool(send_draft)
    mcp.add_tool(list_drafts)
    mcp.add_tool(delete_draft)
    mcp.add_tool(get_user_info)
    mcp.add_tool(list_emails)
    mcp.add_tool(get_email)
    mcp.add_tool(mark_as_read)
    mcp.add_tool(mark_as_unread)

    return mcp


def create_default_server() -> FastMCP:
    """The remote-only server is exported from main.py as mcp."""
    raise RuntimeError("Local stdio server mode has been decommissioned")
```

- [ ] **Step 2: Run server assembly tests**

Run: `pytest tests/test_server_tools.py -v`
Expected: Some tests may fail if they reference `send_email`. We'll fix those in Task 7.

- [ ] **Step 3: Commit**

```bash
git add src/server.py
git commit -m "feat: add inbox tools, expose delete_draft, remove send_email and guidance registration"
```

---

### Task 5: Delete guidance and resources trees

**Files:**
- Delete: `src/guidance/` (entire directory tree)
- Delete: `src/resources/` (entire directory tree)
- Delete: `tests/test_guidance.py`

- [ ] **Step 1: Delete guidance module**

```bash
rm -rf src/guidance/ src/resources/
rm tests/test_guidance.py
```

- [ ] **Step 2: Verify imports still work**

Run: `uv run python -c "from src.server import create_server; print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add -u src/guidance/ src/resources/ tests/test_guidance.py
git commit -m "refactor: remove static guidance prompts, resources, and tools"
```

---

### Task 6: Update src/__init__.py

**Files:**
- Modify: `src/__init__.py`

- [ ] **Step 1: Add new model exports**

```python
"""Gmail MCP Server - Core package."""

__version__ = "0.1.0"

from .gmail_gateway import GmailError, GmailGateway
from .gmail_session import GmailSession, GmailSessionFactory
from .mail_composer import MailComposer
from .models import (
    EmailRequest,
    EmailResponse,
    DraftInfo,
    UserInfo,
    EmailListItem,
    EmailDetail,
    EmailAddress,
    AttachmentInfo,
)

__all__ = [
    "GmailGateway",
    "GmailError",
    "GmailSession",
    "GmailSessionFactory",
    "MailComposer",
    "EmailRequest",
    "EmailResponse",
    "DraftInfo",
    "UserInfo",
    "EmailListItem",
    "EmailDetail",
    "EmailAddress",
    "AttachmentInfo",
]
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from src import EmailListItem, EmailDetail; print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add src/__init__.py
git commit -m "feat: export new email-reader models from package"
```

---

### Task 7: Update tests for new tool set

**Files:**
- Modify: `tests/test_server_tools.py`

- [ ] **Step 1: Update test_server_tools.py**

```python
"""Tests for server assembly."""

from unittest.mock import MagicMock

import pytest

from src.server import create_server, get_authenticated_session
from src.gmail_session import CurrentGmailSessionFactory


class TestCreateServer:
    def test_creates_fastmcp_instance(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        assert mcp.name == "Gmail MCP Server"

    def test_sets_session_factory(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        create_server(fake_factory)

        assert (
            get_authenticated_session()
            == fake_factory.create_current_session.return_value
        )

    def test_import_has_no_side_effects(self):
        """Importing src.server must not create mcp or touch filesystem."""
        import src.server as server_module

        server_module._session_factory = None

        assert server_module._session_factory is None

    def test_missing_session_returns_auth_error(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        fake_factory.create_current_session.return_value = None
        mcp = create_server(fake_factory)

        import asyncio

        with pytest.raises(Exception, match="No authorized Google user"):
            asyncio.run(
                mcp.call_tool("create_draft", {"to": "a", "subject": "b", "body": "c"})
            )

    def test_registers_all_nine_tools(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        tool_names = {t.name for t in mcp.get_tools()}

        expected = {
            "create_draft",
            "send_draft",
            "list_drafts",
            "delete_draft",
            "get_user_info",
            "list_emails",
            "get_email",
            "mark_as_read",
            "mark_as_unread",
        }
        assert tool_names == expected

    def test_send_email_is_not_registered(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        tool_names = {t.name for t in mcp.get_tools()}
        assert "send_email" not in tool_names

    def test_no_guidance_registrations_remain(self):
        """Verify no guidance tools, prompts, or resources are registered."""
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        tool_names = {t.name for t in mcp.get_tools()}
        assert "get_subject_line_help" not in tool_names
        assert "validate_subject_line_tool" not in tool_names
        assert "get_email_templates" not in tool_names
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_server_tools.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_server_tools.py
git commit -m "test: update server tests for new tool set, add tool count verification"
```

---

### Task 8: Final verification

**Files:**
- None

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 2: Run ruff check**

Run: `uv run ruff check .`
Expected: No errors (or only pre-existing ones unrelated to our changes)

- [ ] **Step 3: Run lint/format**

Run: `uv run ruff format --check .`
Expected: All files already formatted

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```
