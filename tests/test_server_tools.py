"""Tests for server assembly."""

import asyncio
from unittest.mock import MagicMock

import pytest

from src.server import create_server, get_authenticated_session
from src.gmail_session import CurrentGmailSessionFactory


class TestCreateServer:
    def test_creates_fastmcp_instance(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        assert mcp.name == "Gmail MCP Server"

    def test_sets_session_factory(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        create_server(fake_factory)

        assert (
            get_authenticated_session()
            == fake_factory.create_current_session.return_value
        )

    def test_import_has_no_side_effects(self):
        import src.server as server_module

        server_module._session_factory = None

        assert server_module._session_factory is None

    def test_missing_session_returns_error(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        fake_factory.create_current_session.return_value = None
        mcp = create_server(fake_factory)

        with pytest.raises(Exception, match="Gmail session not available"):
            asyncio.run(
                mcp.call_tool("get_user_info", {})
            )

    def test_registers_expected_tools(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert "get_user_info" in tool_names
        assert "create_draft" in tool_names
        assert "send_draft" in tool_names
        assert "list_drafts" in tool_names
        assert "delete_draft" in tool_names
        assert "list_emails" in tool_names
        assert "get_email" in tool_names
        assert "mark_as_read" in tool_names
        assert "mark_as_unread" in tool_names

    def test_send_email_not_registered(self):
        fake_factory = MagicMock(spec=CurrentGmailSessionFactory)
        mcp = create_server(fake_factory)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert "send_email" not in tool_names
