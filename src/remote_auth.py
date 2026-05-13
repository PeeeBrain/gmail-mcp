"""Remote Google OAuth session factory for Horizon deployments."""

from google.oauth2.credentials import Credentials

from fastmcp.server.dependencies import get_access_token

from .gmail_session import GmailSession, GmailSessionFactory


class ForbiddenGmailIdentityError(Exception):
    """Raised when the authenticated Google user is not the allowed Gmail user."""


class RemoteGoogleSessionFactory:
    """Creates Gmail sessions from the current FastMCP Google access token."""

    def __init__(self, allowed_gmail_email: str):
        self.allowed_gmail_email = allowed_gmail_email.strip().lower()
        self._session_factory = GmailSessionFactory()

    def create_current_session(self) -> GmailSession | None:
        token = get_access_token()
        if token is None:
            return None

        email = str(token.claims.get("email") or "").strip().lower()
        if email != self.allowed_gmail_email:
            raise ForbiddenGmailIdentityError(
                "Authenticated Google user is not allowed to use this Gmail server"
            )

        credentials = Credentials(token=token.token, scopes=token.scopes)
        return self._session_factory.create_session(credentials)
