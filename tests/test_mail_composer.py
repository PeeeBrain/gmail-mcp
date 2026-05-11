"""Tests for mail_composer module."""

import base64
from email import message_from_bytes
from email import policy

import pytest

from src.mail_composer import MailComposer
from src.models import EmailRequest


class TestMailComposer:
    """Tests for the MailComposer class."""

    @pytest.fixture
    def composer(self):
        return MailComposer()

    def test_plain_text_email(self, composer):
        request = EmailRequest(to="alice@example.com", subject="Hello", body="World")
        sender = "bob@example.com"

        raw = composer.compose(request, sender)

        message = _decode_raw_message(raw)
        assert message["To"] == "alice@example.com"
        assert message["From"] == "bob@example.com"
        assert message["Subject"] == "Hello"
        assert message.get_content_type() == "text/plain"
        assert message.get_content().strip() == "World"

    def test_html_email(self, composer):
        request = EmailRequest(
            to="alice@example.com",
            subject="Hello",
            body="Plain text",
            html_body="<b>HTML</b>",
        )
        sender = "bob@example.com"

        raw = composer.compose(request, sender)

        message = _decode_raw_message(raw)
        assert message["To"] == "alice@example.com"
        assert message["From"] == "bob@example.com"
        assert message["Subject"] == "Hello"
        assert message.is_multipart()
        parts = list(message.iter_parts())
        assert len(parts) == 2
        assert parts[0].get_content_type() == "text/plain"
        assert parts[0].get_content().strip() == "Plain text"
        assert parts[1].get_content_type() == "text/html"
        assert parts[1].get_content().strip() == "<b>HTML</b>"

    def test_cc_and_bcc_present(self, composer):
        request = EmailRequest(
            to="alice@example.com",
            subject="Hello",
            body="World",
            cc="carol@example.com",
            bcc="dave@example.com",
        )
        sender = "bob@example.com"

        raw = composer.compose(request, sender)

        message = _decode_raw_message(raw)
        assert message["Cc"] == "carol@example.com"
        assert message["Bcc"] == "dave@example.com"

    def test_cc_and_bcc_absent(self, composer):
        request = EmailRequest(to="alice@example.com", subject="Hello", body="World")
        sender = "bob@example.com"

        raw = composer.compose(request, sender)

        message = _decode_raw_message(raw)
        assert "Cc" not in message
        assert "Bcc" not in message

    def test_encoded_payload_decodes_valid_email(self, composer):
        request = EmailRequest(to="alice@example.com", subject="Test", body="Body text")
        sender = "bob@example.com"

        raw = composer.compose(request, sender)

        message = _decode_raw_message(raw)
        assert message["To"] == "alice@example.com"
        assert message["Subject"] == "Test"
        assert message.get_content_type() == "text/plain"
        assert message.get_content().strip() == "Body text"


def _decode_raw_message(raw: str):
    decoded_bytes = base64.urlsafe_b64decode(raw.encode("utf-8"))
    return message_from_bytes(decoded_bytes, policy=policy.default)
