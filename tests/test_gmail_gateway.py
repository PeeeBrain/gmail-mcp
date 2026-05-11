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
