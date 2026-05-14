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
