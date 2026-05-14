"""Tests for gmail_gateway module."""

from unittest.mock import MagicMock

import pytest

from googleapiclient.errors import HttpError

from src.gmail_gateway import GmailError, GmailGateway
from src.models import DraftInfo, EmailResponse, UserInfo


class FakeResp:
    status = 403
    reason = "Forbidden"


@pytest.fixture
def mock_service():
    """Return a fully mocked Gmail API service."""
    return MagicMock()


@pytest.fixture
def gateway(mock_service):
    """Return a GmailGateway backed by a mock service."""
    fake_creds = MagicMock()
    return GmailGateway(fake_creds, service=mock_service)


class TestGetProfile:
    def test_returns_user_info(self, gateway, mock_service):
        mock_service.users().getProfile().execute.return_value = {
            "emailAddress": "alice@example.com",
            "messagesTotal": 42,
            "threadsTotal": 7,
        }

        result = gateway.get_profile()

        assert result == UserInfo(
            email="alice@example.com", messages_total=42, threads_total=7
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().getProfile().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to get user profile"):
            gateway.get_profile()


class TestSendRawMessage:
    def test_returns_email_response(self, gateway, mock_service):
        mock_service.users().messages().send.return_value.execute.return_value = {
            "id": "msg123",
            "threadId": "thread456",
        }

        result = gateway.send_raw_message("raw-payload")

        assert result == EmailResponse(
            id="msg123", thread_id="thread456", status="sent"
        )
        mock_service.users().messages().send.assert_called_once_with(
            userId="me", body={"raw": "raw-payload"}
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().send().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to send email"):
            gateway.send_raw_message("raw")


class TestCreateRawDraft:
    def test_returns_email_response(self, gateway, mock_service):
        mock_service.users().drafts().create.return_value.execute.return_value = {
            "id": "draft789",
            "message": {"id": "msg123", "threadId": "thread456"},
        }

        result = gateway.create_raw_draft("raw-payload")

        assert result == EmailResponse(
            id="draft789", thread_id="thread456", status="draft"
        )
        mock_service.users().drafts().create.assert_called_once_with(
            userId="me", body={"message": {"raw": "raw-payload"}}
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().drafts().create().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to create draft"):
            gateway.create_raw_draft("raw")


class TestSendDraft:
    def test_returns_email_response(self, gateway, mock_service):
        mock_service.users().drafts().send.return_value.execute.return_value = {
            "id": "msg123",
            "threadId": "thread456",
        }

        result = gateway.send_draft("draft789")

        assert result == EmailResponse(
            id="msg123", thread_id="thread456", status="sent"
        )
        mock_service.users().drafts().send.assert_called_once_with(
            userId="me", body={"id": "draft789"}
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().drafts().send().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to send draft"):
            gateway.send_draft("draft789")


class TestListDrafts:
    def test_maps_headers_and_snippets(self, gateway, mock_service):
        mock_service.users().drafts().list.return_value.execute.return_value = {
            "drafts": [{"id": "draft1"}]
        }
        mock_service.users().drafts().get.return_value.execute.return_value = {
            "message": {
                "id": "msg1",
                "threadId": "t1",
                "snippet": "Hello...",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test Subject"},
                        {"name": "To", "value": "alice@example.com"},
                    ]
                },
            }
        }

        result = gateway.list_drafts(max_results=5)

        assert result == [
            DraftInfo(
                id="draft1",
                message_id="msg1",
                thread_id="t1",
                subject="Test Subject",
                to="alice@example.com",
                snippet="Hello...",
            )
        ]
        mock_service.users().drafts().list.assert_called_once_with(
            userId="me", maxResults=5
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().drafts().list().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to list drafts"):
            gateway.list_drafts()


class TestListMessages:
    def test_returns_email_list_items(self, gateway, mock_service):
        mock_service.users().messages().list.return_value.execute.return_value = {
            "messages": [
                {"id": "msg1", "threadId": "t1"},
                {"id": "msg2", "threadId": "t2"},
            ],
            "nextPageToken": "tok",
            "resultSizeEstimate": 2,
        }
        get_returns = [
            {
                "id": "msg1",
                "threadId": "t1",
                "labelIds": ["INBOX", "UNREAD"],
                "snippet": "Hello world",
                "internalDate": "1715700000000",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test"},
                        {"name": "From", "value": "alice@example.com"},
                        {"name": "To", "value": "bob@example.com"},
                        {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                    ]
                },
            },
            {
                "id": "msg2",
                "threadId": "t2",
                "labelIds": ["INBOX"],
                "snippet": "Another",
                "internalDate": "1715700000001",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Re: Test"},
                        {"name": "From", "value": "bob@example.com"},
                        {"name": "To", "value": "alice@example.com"},
                        {"name": "Date", "value": "Tue, 14 May 2026 11:00:00 +0000"},
                    ]
                },
            },
        ]
        mock_service.users().messages().get.return_value.execute.side_effect = get_returns

        result = gateway.list_messages(query="is:unread", max_results=10)

        mock_service.users().messages().list.assert_called_once_with(
            userId="me", q="is:unread", maxResults=10,
            includeSpamTrash=False,
        )
        assert len(result) == 2
        assert result[0].id == "msg1"
        assert result[0].subject == "Test"
        assert result[0].from_ == "alice@example.com"
        assert result[0].snippet == "Hello world"
        assert "UNREAD" in result[0].label_ids

    def test_handles_empty_results(self, gateway, mock_service):
        mock_service.users().messages().list.return_value.execute.return_value = {}

        result = gateway.list_messages()

        assert result == []

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().list().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to list messages"):
            gateway.list_messages()


class TestGetMessage:
    def test_returns_email_detail(self, gateway, mock_service):
        mock_service.users().messages().get.return_value.execute.return_value = {
            "id": "msg1",
            "threadId": "t1",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Hello world",
            "internalDate": "1715700000000",
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "From", "value": "Alice <alice@example.com>"},
                    {"name": "To", "value": "Bob <bob@example.com>"},
                    {"name": "Cc", "value": "Carol <carol@example.com>"},
                    {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                ],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                    {"mimeType": "text/html", "body": {"data": "PGgxPkhlbGxvPC9oMT4="}},
                    {
                        "mimeType": "application/pdf",
                        "filename": "report.pdf",
                        "body": {"attachmentId": "att1"},
                    },
                ],
            },
        }

        result = gateway.get_message("msg1")

        assert result.id == "msg1"
        assert result.subject == "Test Email"
        assert result.from_.email == "alice@example.com"
        assert result.from_.name == "Alice"
        assert result.to[0].email == "bob@example.com"
        assert result.to[0].name == "Bob"
        assert result.cc[0].email == "carol@example.com"
        assert result.body_text == "Hello"
        assert result.body_html == "<h1>Hello</h1>"
        assert result.attachments[0].filename == "report.pdf"
        assert result.attachments[0].mime_type == "application/pdf"

    def test_handles_simple_text_body(self, gateway, mock_service):
        mock_service.users().messages().get.return_value.execute.return_value = {
            "id": "msg1",
            "threadId": "t1",
            "labelIds": ["INBOX"],
            "snippet": "Hi",
            "internalDate": "1715700000000",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Hi"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "To", "value": "bob@example.com"},
                    {"name": "Date", "value": "Tue, 14 May 2026 10:00:00 +0000"},
                ],
                "body": {"data": "SGk="},
            },
        }

        result = gateway.get_message("msg1")

        assert result.body_text == "Hi"
        assert result.body_html == ""
        assert result.attachments == []

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().get().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to get message"):
            gateway.get_message("msg1")


class TestModifyLabels:
    def test_modifies_labels(self, gateway, mock_service):
        mock_service.users().messages().modify.return_value.execute.return_value = {
            "id": "msg1",
            "labelIds": ["INBOX"],
        }

        result = gateway.modify_labels(
            "msg1", add_label_ids=["STARRED"], remove_label_ids=["UNREAD"]
        )

        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": ["STARRED"], "removeLabelIds": ["UNREAD"]},
        )

    def test_handles_remove_only(self, gateway, mock_service):
        mock_service.users().messages().modify.return_value.execute.return_value = {
            "id": "msg1",
            "labelIds": [],
        }

        result = gateway.modify_labels("msg1", remove_label_ids=["UNREAD"])

        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": [], "removeLabelIds": ["UNREAD"]},
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().messages().modify().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to modify labels"):
            gateway.modify_labels("msg1", add_label_ids=["STARRED"])


class TestDeleteDraft:
    def test_returns_true(self, gateway, mock_service):
        mock_service.users().drafts().delete.return_value.execute.return_value = None

        result = gateway.delete_draft("draft1")

        assert result is True
        mock_service.users().drafts().delete.assert_called_once_with(
            userId="me", id="draft1"
        )

    def test_http_error_becomes_gmail_error(self, gateway, mock_service):
        mock_service.users().drafts().delete().execute.side_effect = HttpError(
            FakeResp(), b"oops"
        )

        with pytest.raises(GmailError, match="Failed to delete draft"):
            gateway.delete_draft("draft1")
