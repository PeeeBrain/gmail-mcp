"""Gmail Gateway - isolates Google API calls and error translation."""

from typing import List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .models import (
    AttachmentInfo,
    DraftInfo,
    EmailAddress,
    EmailDetail,
    EmailListItem,
    EmailResponse,
    UserInfo,
)


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

    def list_messages(
        self,
        query: str = "",
        label_ids: list[str] | None = None,
        max_results: int = 20,
        include_spam_trash: bool = False,
        page_token: str | None = None,
    ) -> List["EmailListItem"]:
        """List messages matching query and label filters.

        Uses Gmail's native search syntax for the query parameter.
        """
        try:
            kwargs: dict = {
                "userId": "me",
                "q": query,
                "maxResults": max_results,
                "includeSpamTrash": include_spam_trash,
            }
            if label_ids:
                kwargs["labelIds"] = label_ids
            if page_token:
                kwargs["pageToken"] = page_token

            results = (
                self._service.users().messages().list(**kwargs).execute()
            )

            messages = results.get("messages", [])
            items: List[EmailListItem] = []

            for msg in messages:
                detail = (
                    self._service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["Subject", "From", "To", "Date"],
                    )
                    .execute()
                )

                headers = detail.get("payload", {}).get("headers", [])
                header_map = {h["name"]: h["value"] for h in headers}

                items.append(
                    EmailListItem.model_validate(
                        {
                            "id": detail["id"],
                            "thread_id": detail["threadId"],
                            "label_ids": detail.get("labelIds", []),
                            "snippet": detail.get("snippet", ""),
                            "subject": header_map.get("Subject", "No Subject"),
                            "from": header_map.get("From", "Unknown"),
                            "to": header_map.get("To", ""),
                            "date": header_map.get("Date", ""),
                            "internal_date": detail.get("internalDate", ""),
                        }
                    )
                )

            return items

        except HttpError as e:
            raise GmailError(f"Failed to list messages: {e}")

    def get_message(self, email_id: str) -> "EmailDetail":
        """Get full message content by ID."""
        try:
            detail = (
                self._service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            payload = detail.get("payload", {})
            headers = payload.get("headers", [])
            header_map = {h["name"]: h["value"] for h in headers}

            body_text, body_html, attachments = self._parse_parts(payload)

            return EmailDetail.model_validate(
                {
                    "id": detail["id"],
                    "thread_id": detail["threadId"],
                    "label_ids": detail.get("labelIds", []),
                    "snippet": detail.get("snippet", ""),
                    "subject": header_map.get("Subject", "No Subject"),
                    "from": {
                        "name": self._parse_email_address(header_map.get("From", "")).name,
                        "email": self._parse_email_address(header_map.get("From", "")).email,
                    },
                    "to": [
                        {"name": a.name, "email": a.email}
                        for a in self._parse_email_addresses(header_map.get("To", ""))
                    ],
                    "cc": [
                        {"name": a.name, "email": a.email}
                        for a in self._parse_email_addresses(header_map.get("Cc", ""))
                    ],
                    "bcc": [
                        {"name": a.name, "email": a.email}
                        for a in self._parse_email_addresses(header_map.get("Bcc", ""))
                    ],
                    "date": header_map.get("Date", ""),
                    "internal_date": detail.get("internalDate", ""),
                    "body_text": body_text,
                    "body_html": body_html,
                    "attachments": [
                        {"filename": a.filename, "mime_type": a.mime_type}
                        for a in attachments
                    ],
                }
            )

        except HttpError as e:
            raise GmailError(f"Failed to get message: {e}")

    def modify_labels(
        self,
        email_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> bool:
        """Add or remove labels on a message."""
        try:
            self._service.users().messages().modify(
                userId="me",
                id=email_id,
                body={
                    "addLabelIds": add_label_ids or [],
                    "removeLabelIds": remove_label_ids or [],
                },
            ).execute()
            return True
        except HttpError as e:
            raise GmailError(f"Failed to modify labels: {e}")

    @staticmethod
    def _parse_email_address(header_value: str):
        """Parse a single email address header value (e.g. 'Alice <alice@example.com>')."""
        import re
        match = re.match(r"(.+?)\s*<(.+?)>", header_value)
        if match:
            return EmailAddress(name=match.group(1).strip(), email=match.group(2).strip())
        return EmailAddress(email=header_value.strip())

    @staticmethod
    def _parse_email_addresses(header_value: str) -> list:
        """Parse multiple email addresses from a header value."""
        if not header_value:
            return []
        import re
        addresses = []
        for part in re.split(r",\s*(?=[^<]*<|[^,]+@)", header_value):
            part = part.strip()
            if part:
                match = re.match(r"(.+?)\s*<(.+?)>", part)
                if match:
                    addresses.append(
                        EmailAddress(
                            name=match.group(1).strip(),
                            email=match.group(2).strip(),
                        )
                    )
                else:
                    addresses.append(EmailAddress(email=part))
        return addresses

    @staticmethod
    def _parse_parts(payload: dict) -> tuple:
        """Extract text body, html body, and attachment list from message payload.

        Returns (body_text: str, body_html: str, attachments: list[AttachmentInfo])
        """
        import base64

        body_text = ""
        body_html = ""
        attachments: list = []

        parts = payload.get("parts", [])

        if payload.get("mimeType") == "text/plain" and not parts:
            data = payload.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(
                    data + "=" * (-len(data) % 4)
                ).decode("utf-8", errors="replace")
            return body_text, body_html, attachments

        if payload.get("mimeType") == "text/html" and not parts:
            data = payload.get("body", {}).get("data", "")
            if data:
                body_html = base64.urlsafe_b64decode(
                    data + "=" * (-len(data) % 4)
                ).decode("utf-8", errors="replace")
            return body_text, body_html, attachments

        for part in parts:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(
                        data + "=" * (-len(data) % 4)
                    ).decode("utf-8", errors="replace")
            elif mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_html = base64.urlsafe_b64decode(
                        data + "=" * (-len(data) % 4)
                    ).decode("utf-8", errors="replace")
            elif part.get("filename") and part.get("body", {}).get("attachmentId"):
                attachments.append(
                    AttachmentInfo(
                        filename=part["filename"],
                        mime_type=mime_type,
                    )
                )
            elif "parts" in part:
                sub_text, sub_html, sub_att = GmailGateway._parse_parts(part)
                if sub_text:
                    body_text = sub_text
                if sub_html:
                    body_html = sub_html
                attachments.extend(sub_att)

        return body_text, body_html, attachments
