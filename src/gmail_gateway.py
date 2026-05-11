"""Gmail Gateway - isolates Google API calls and error translation."""

from typing import List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .models import DraftInfo, EmailResponse, UserInfo


class GmailError(Exception):
    """Project-level error for Gmail API failures."""


class GmailGateway:
    """Isolated adapter for Google Gmail API v1."""

    def __init__(self, credentials: Credentials, service=None):
        self.credentials = credentials
        self._service = service or build("gmail", "v1", credentials=credentials)

    def get_profile(self) -> UserInfo:
        """Get current user's Gmail profile."""
        try:
            profile = self._service.users().getProfile(userId="me").execute()
            return UserInfo(
                email=profile.get("emailAddress", ""),
                messages_total=profile.get("messagesTotal", 0),
                threads_total=profile.get("threadsTotal", 0),
            )
        except HttpError as e:
            raise GmailError(f"Failed to get user profile: {e}")

    def send_raw_message(self, raw: str) -> EmailResponse:
        """Send a base64url-encoded raw message."""
        try:
            sent = (
                self._service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )
            return EmailResponse(
                id=sent["id"],
                thread_id=sent["threadId"],
                status="sent",
            )
        except HttpError as e:
            raise GmailError(f"Failed to send email: {e}")

    def create_raw_draft(self, raw: str) -> EmailResponse:
        """Create a draft from a base64url-encoded raw message."""
        try:
            draft = (
                self._service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw}})
                .execute()
            )
            message = draft["message"]
            return EmailResponse(
                id=draft["id"],
                thread_id=message["threadId"],
                status="draft",
            )
        except HttpError as e:
            raise GmailError(f"Failed to create draft: {e}")

    def send_draft(self, draft_id: str) -> EmailResponse:
        """Send an existing draft."""
        try:
            sent = (
                self._service.users()
                .drafts()
                .send(userId="me", body={"id": draft_id})
                .execute()
            )
            return EmailResponse(
                id=sent["id"],
                thread_id=sent["threadId"],
                status="sent",
            )
        except HttpError as e:
            raise GmailError(f"Failed to send draft: {e}")

    def list_drafts(self, max_results: int = 10) -> List[DraftInfo]:
        """List email drafts."""
        try:
            results = (
                self._service.users()
                .drafts()
                .list(userId="me", maxResults=max_results)
                .execute()
            )

            drafts = results.get("drafts", [])
            draft_list: List[DraftInfo] = []

            for draft in drafts:
                detail = (
                    self._service.users()
                    .drafts()
                    .get(userId="me", id=draft["id"])
                    .execute()
                )

                message = detail["message"]
                headers = message.get("payload", {}).get("headers", [])

                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                to = next(
                    (h["value"] for h in headers if h["name"] == "To"),
                    "Unknown",
                )

                draft_list.append(
                    DraftInfo(
                        id=draft["id"],
                        message_id=message["id"],
                        thread_id=message["threadId"],
                        subject=subject,
                        to=to,
                        snippet=message.get("snippet", ""),
                    )
                )

            return draft_list

        except HttpError as e:
            raise GmailError(f"Failed to list drafts: {e}")

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft."""
        try:
            self._service.users().drafts().delete(userId="me", id=draft_id).execute()
            return True
        except HttpError as e:
            raise GmailError(f"Failed to delete draft: {e}")
