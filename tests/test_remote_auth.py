"""Tests for server-owned Gmail session creation."""

import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("GOOGLE_OAUTH_CLIENT_ID", "client-id")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
os.environ.setdefault("GOOGLE_OAUTH_REFRESH_TOKEN", "refresh-token")
os.environ.setdefault("ALLOWED_GMAIL_EMAIL", "owner@example.com")

from remote import _required_env
from src.remote_auth import (
    GMAIL_MODIFY_SCOPE,
    GMAIL_SEND_SCOPE,
    GOOGLE_TOKEN_URI,
    OwnerGmailSessionFactory,
)


def test_required_env_strips_surrounding_whitespace(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SECRET", "  secret-value\n")

    assert _required_env("EXAMPLE_SECRET") == "secret-value"


def test_required_env_rejects_blank_values(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SECRET", "  \n")

    with pytest.raises(RuntimeError, match="EXAMPLE_SECRET must be set"):
        _required_env("EXAMPLE_SECRET")


def test_owner_factory_creates_session_from_refresh_token(monkeypatch):
    session = MagicMock()
    create_session = MagicMock(return_value=session)
    monkeypatch.setattr(
        "src.remote_auth.GmailSessionFactory.create_session", create_session
    )

    factory = OwnerGmailSessionFactory(
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        allowed_gmail_email="owner@example.com",
    )

    result = factory.create_current_session()

    assert result is session
    credentials = create_session.call_args.args[0]
    assert credentials.refresh_token == "refresh-token"
    assert credentials.token_uri == GOOGLE_TOKEN_URI
    assert credentials.client_id == "client-id"
    assert credentials.client_secret == "client-secret"
    assert credentials.scopes == [GMAIL_SEND_SCOPE, GMAIL_MODIFY_SCOPE]


def test_validate_allowed_identity_accepts_matching_owner(monkeypatch):
    session = MagicMock()
    session.get_user_info.return_value = {"email": "Owner@Example.com"}
    monkeypatch.setattr(
        "src.remote_auth.OwnerGmailSessionFactory.create_current_session",
        lambda self: session,
    )

    factory = OwnerGmailSessionFactory(
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        allowed_gmail_email="owner@example.com",
    )

    factory.validate_allowed_identity()


def test_validate_allowed_identity_rejects_mismatched_owner(monkeypatch):
    session = MagicMock()
    session.get_user_info.return_value = {"email": "other@example.com"}
    monkeypatch.setattr(
        "src.remote_auth.OwnerGmailSessionFactory.create_current_session",
        lambda self: session,
    )

    factory = OwnerGmailSessionFactory(
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        allowed_gmail_email="owner@example.com",
    )

    try:
        factory.validate_allowed_identity()
    except RuntimeError as exc:
        assert "does not belong to ALLOWED_GMAIL_EMAIL" in str(exc)
    else:
        raise AssertionError("expected mismatched owner to be rejected")
