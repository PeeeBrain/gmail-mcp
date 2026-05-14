"""Gmail operation session for the selected local Gmail user."""

from typing import Protocol, List, Optional

from google.oauth2.credentials import Credentials

from .gmail_gateway import GmailGateway
from .mail_composer import MailComposer
from .models import EmailRequest


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
        return [item.model_dump(by_alias=True) for item in items]

    def get_email(self, email_id: str):
        return self._gateway.get_message(email_id).model_dump(by_alias=True)

    def mark_as_read(self, email_id: str) -> bool:
        return self._gateway.modify_labels(
            email_id, remove_label_ids=["UNREAD"]
        )

    def mark_as_unread(self, email_id: str) -> bool:
        return self._gateway.modify_labels(
            email_id, add_label_ids=["UNREAD"]
        )


class GmailSessionFactory:
    """Creates Gmail sessions from Google OAuth credentials."""

    def create_session(self, credentials: Credentials) -> GmailSession:
        gateway = GmailGateway(credentials)
        composer = MailComposer()
        return GmailSession(gateway, composer)


class CurrentGmailSessionFactory(Protocol):
    """Creates a Gmail session for the current MCP request or process."""

    def create_current_session(self) -> GmailSession | None:
        """Return a Gmail session, or None when Gmail is not authorized."""
        ...
