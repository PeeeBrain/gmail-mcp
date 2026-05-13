"""Tests for remote Google OAuth session creation."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.remote_auth import ForbiddenGmailIdentityError, RemoteGoogleSessionFactory


def test_remote_factory_returns_none_without_access_token(monkeypatch):
    monkeypatch.setattr("src.remote_auth.get_access_token", lambda: None)

    factory = RemoteGoogleSessionFactory("owner@example.com")

    assert factory.create_current_session() is None


def test_remote_factory_rejects_unallowed_google_user(monkeypatch):
    token = SimpleNamespace(
        token="access-token",
        scopes=["https://www.googleapis.com/auth/gmail.send"],
        claims={"email": "other@example.com"},
    )
    monkeypatch.setattr("src.remote_auth.get_access_token", lambda: token)

    factory = RemoteGoogleSessionFactory("owner@example.com")

    with pytest.raises(ForbiddenGmailIdentityError):
        factory.create_current_session()


def test_remote_factory_creates_session_for_allowed_google_user(monkeypatch):
    token = SimpleNamespace(
        token="access-token",
        scopes=["https://www.googleapis.com/auth/gmail.send"],
        claims={"email": "Owner@Example.com"},
    )
    session = MagicMock()
    monkeypatch.setattr("src.remote_auth.get_access_token", lambda: token)
    create_session = MagicMock(return_value=session)
    monkeypatch.setattr(
        "src.remote_auth.GmailSessionFactory.create_session", create_session
    )

    factory = RemoteGoogleSessionFactory("owner@example.com")
    result = factory.create_current_session()

    assert result is session
    credentials = create_session.call_args.args[0]
    assert credentials.token == "access-token"
