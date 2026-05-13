"""Prefect Horizon entry point for the remote Gmail MCP server."""

import os

from fastmcp.server.auth.providers.google import GoogleProvider

from src.remote_auth import RemoteGoogleSessionFactory
from src.server import create_server

GOOGLE_IDENTITY_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"

REQUIRED_GOOGLE_SCOPES = [
    "openid",
    GOOGLE_IDENTITY_SCOPE,
    GMAIL_SEND_SCOPE,
    GMAIL_MODIFY_SCOPE,
]


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be set for the remote Gmail MCP server")
    return value


def create_remote_server():
    """Create the Google-protected remote MCP server for Horizon."""
    auth = GoogleProvider(
        client_id=_required_env("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=_required_env("GOOGLE_OAUTH_CLIENT_SECRET"),
        base_url=_required_env("GMAIL_MCP_BASE_URL"),
        required_scopes=REQUIRED_GOOGLE_SCOPES,
        jwt_signing_key=os.environ.get("FASTMCP_JWT_SIGNING_KEY"),
    )
    session_factory = RemoteGoogleSessionFactory(
        allowed_gmail_email=_required_env("ALLOWED_GMAIL_EMAIL")
    )
    return create_server(session_factory, auth=auth)


mcp = create_remote_server()
