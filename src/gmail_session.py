"""Gmail operation session for the selected local Gmail user."""

from google.oauth2.credentials import Credentials

from .gmail_client import GmailClient
from .token_store import GmailTokenStore


class GmailSession(GmailClient):
    """Ready-to-use Gmail operations for one current Gmail user."""


class GmailSessionFactory:
    """Creates Gmail sessions from the local token store."""

    def __init__(self, token_store: GmailTokenStore):
        self.token_store = token_store

    def create_current_session(self) -> GmailSession | None:
        credentials = self.token_store.get_credentials()
        if not credentials:
            return None
        return self.create_session(credentials)

    def create_session(self, credentials: Credentials) -> GmailSession:
        return GmailSession(credentials)
