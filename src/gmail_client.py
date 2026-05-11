"""Gmail API client wrapper for sending emails."""

from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .mail_composer import MailComposer
from .models import EmailRequest


class GmailClient:
    """Gmail API client for email operations."""

    def __init__(self, credentials: Credentials):
        """Initialize Gmail client with OAuth2 credentials."""
        self.credentials = credentials
        self.service = build("gmail", "v1", credentials=credentials)
        self._composer = MailComposer()

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user's Gmail profile information."""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return {
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal", 0),
                "threads_total": profile.get("threadsTotal", 0),
            }
        except HttpError as e:
            raise Exception(f"Failed to get user info: {e}")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        html_body: str | None = None,
    ) -> Dict[str, Any]:
        """Send an email message."""
        try:
            request = EmailRequest(
                to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
            )
            sender = self.get_user_info()["email"]
            raw_message = self._composer.compose(request, sender)

            send_message = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            return {
                "id": send_message["id"],
                "thread_id": send_message["threadId"],
                "status": "sent",
            }

        except HttpError as e:
            raise Exception(f"Failed to send email: {e}")

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        html_body: str | None = None,
    ) -> Dict[str, Any]:
        """Create an email draft."""
        try:
            request = EmailRequest(
                to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
            )
            sender = self.get_user_info()["email"]
            raw_message = self._composer.compose(request, sender)

            draft = (
                self.service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw_message}})
                .execute()
            )

            return {
                "id": draft["id"],
                "message_id": draft["message"]["id"],
                "thread_id": draft["message"]["threadId"],
                "status": "draft",
            }

        except HttpError as e:
            raise Exception(f"Failed to create draft: {e}")

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        """Send an existing draft."""
        try:
            sent_message = (
                self.service.users()
                .drafts()
                .send(userId="me", body={"id": draft_id})
                .execute()
            )

            return {
                "id": sent_message["id"],
                "thread_id": sent_message["threadId"],
                "status": "sent",
            }

        except HttpError as e:
            raise Exception(f"Failed to send draft: {e}")

    def list_drafts(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List email drafts."""
        try:
            results = (
                self.service.users()
                .drafts()
                .list(userId="me", maxResults=max_results)
                .execute()
            )

            drafts = results.get("drafts", [])
            draft_list = []

            for draft in drafts:
                # Get draft details
                draft_detail = (
                    self.service.users()
                    .drafts()
                    .get(userId="me", id=draft["id"])
                    .execute()
                )

                message = draft_detail["message"]
                headers = message.get("payload", {}).get("headers", [])

                # Extract subject and to fields
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                to = next((h["value"] for h in headers if h["name"] == "To"), "Unknown")

                draft_list.append(
                    {
                        "id": draft["id"],
                        "message_id": message["id"],
                        "thread_id": message["threadId"],
                        "subject": subject,
                        "to": to,
                        "snippet": message.get("snippet", ""),
                    }
                )

            return draft_list

        except HttpError as e:
            raise Exception(f"Failed to list drafts: {e}")

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft."""
        try:
            self.service.users().drafts().delete(userId="me", id=draft_id).execute()
            return True

        except HttpError as e:
            raise Exception(f"Failed to delete draft: {e}")
