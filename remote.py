"""Prefect Horizon entry point for the remote Gmail MCP server."""

import os

from src.remote_auth import OwnerGmailSessionFactory
from src.server import create_server


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} must be set for the remote Gmail MCP server")
    return value.strip()


def create_remote_server():
    """Create the Horizon-hosted MCP server for the owner's Gmail identity."""
    session_factory = OwnerGmailSessionFactory(
        client_id=_required_env("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=_required_env("GOOGLE_OAUTH_CLIENT_SECRET"),
        refresh_token=_required_env("GOOGLE_OAUTH_REFRESH_TOKEN"),
        allowed_gmail_email=_required_env("ALLOWED_GMAIL_EMAIL"),
    )
    return create_server(session_factory)


mcp = create_remote_server()
