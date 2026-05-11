"""Pydantic models for Gmail MCP server."""

from typing import Optional
from pydantic import BaseModel


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
