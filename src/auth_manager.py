"""Compatibility import for the local Gmail token store."""

from .token_store import AuthManager, GmailTokenStore, SCOPES

__all__ = ["AuthManager", "GmailTokenStore", "SCOPES"]
