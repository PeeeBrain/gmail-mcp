"""Gmail operation session for the selected local Gmail user."""

from google.oauth2.credentials import Credentials

from .gmail_gateway import GmailGateway
from .mail_composer import MailComposer
from .models import EmailRequest
from .token_store import GmailTokenStore


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
        gateway = GmailGateway(credentials)
        composer = MailComposer()
        return GmailSession(gateway, composer)
