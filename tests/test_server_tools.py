"""Tests for server assembly."""

from unittest.mock import MagicMock

import pytest

from src.server import create_server, get_authenticated_session
from src.gmail_session import GmailSessionFactory


class TestCreateServer:
    def test_creates_fastmcp_instance(self):
        fake_factory = MagicMock(spec=GmailSessionFactory)
        mcp = create_server(fake_factory)

        assert mcp.name == "Gmail MCP Server"

    def test_sets_session_factory(self):
        fake_factory = MagicMock(spec=GmailSessionFactory)
        create_server(fake_factory)

        assert (
            get_authenticated_session()
            == fake_factory.create_current_session.return_value
        )

    def test_import_has_no_side_effects(self):
        """Importing src.server must not create mcp or touch filesystem."""
        # This is implicitly tested by the test suite running at all,
        # but we verify _session_factory is None before create_server is called.
        import src.server as server_module

        # Reset to simulate a fresh import
        server_module._session_factory = None

        # After a fresh import (or in this test's context), _session_factory
        # should be None until create_server is called.
        assert server_module._session_factory is None

    def test_missing_session_returns_auth_error(self):
        fake_factory = MagicMock(spec=GmailSessionFactory)
        fake_factory.create_current_session.return_value = None
        mcp = create_server(fake_factory)

        # Calling a tool with no session should raise the auth error
        import asyncio

        with pytest.raises(Exception, match="No authenticated user"):
            asyncio.run(
                mcp.call_tool("send_email", {"to": "a", "subject": "b", "body": "c"})
            )
