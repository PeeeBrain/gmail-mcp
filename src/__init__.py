"""Gmail MCP Server - Core package."""

__version__ = "0.1.0"

from .gmail_gateway import GmailError, GmailGateway
from .gmail_session import GmailSession, GmailSessionFactory
from .mail_composer import MailComposer
from .models import EmailRequest, EmailResponse, DraftInfo, UserInfo
from .token_store import AuthManager, GmailTokenStore

__all__ = [
    "AuthManager",
    "GmailTokenStore",
    "GmailGateway",
    "GmailError",
    "GmailSession",
    "GmailSessionFactory",
    "MailComposer",
    "EmailRequest",
    "EmailResponse",
    "DraftInfo",
    "UserInfo",
]
