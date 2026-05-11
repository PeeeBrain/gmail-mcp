"""Gmail MCP Server - Core package."""

__version__ = "0.1.0"

from .gmail_client import GmailClient
from .gmail_session import GmailSession, GmailSessionFactory
from .models import EmailRequest, DraftRequest, EmailResponse, DraftInfo, UserInfo
from .token_store import AuthManager, GmailTokenStore

__all__ = [
    "AuthManager",
    "GmailTokenStore",
    "GmailClient",
    "GmailSession",
    "GmailSessionFactory",
    "EmailRequest",
    "DraftRequest",
    "EmailResponse",
    "DraftInfo",
    "UserInfo",
]
