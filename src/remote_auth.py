"""Server-owned Gmail session factory for Horizon deployments."""

from google.oauth2.credentials import Credentials

from .gmail_session import GmailSession, GmailSessionFactory

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
GMAIL_SCOPES = [GMAIL_SEND_SCOPE, GMAIL_MODIFY_SCOPE]
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


class OwnerGmailSessionFactory:
    """Creates Gmail sessions from the owner's configured Google refresh token."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        allowed_gmail_email: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.allowed_gmail_email = allowed_gmail_email.strip().lower()
        self._session_factory = GmailSessionFactory()

    def create_current_session(self) -> GmailSession | None:
        credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=GMAIL_SCOPES,
        )
        return self._session_factory.create_session(credentials)

    def validate_allowed_identity(self) -> None:
        """Fail fast if the configured Gmail token is not the allowed identity."""
        session = self.create_current_session()
        if session is None:
            raise RuntimeError("Gmail owner credentials are not configured")

        email = session.get_user_info()["email"].strip().lower()
        if email != self.allowed_gmail_email:
            raise RuntimeError(
                "Configured Gmail refresh token does not belong to "
                f"ALLOWED_GMAIL_EMAIL ({self.allowed_gmail_email})"
            )
