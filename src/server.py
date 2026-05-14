"""FastMCP server assembly with tools, prompts, and resources."""

from fastmcp import FastMCP

from .gmail_session import CurrentGmailSessionFactory


_session_factory: CurrentGmailSessionFactory | None = None


def get_authenticated_session():
    """Return a GmailSession or None when no factory is configured."""
    if _session_factory is None:
        return None
    return _session_factory.create_current_session()


def create_server(
    session_factory: CurrentGmailSessionFactory, *, auth=None
) -> FastMCP:
    """Create and assemble a FastMCP Gmail server."""

    global _session_factory
    _session_factory = session_factory

    mcp = FastMCP("Gmail MCP Server", auth=auth)

    add_tool = mcp.add_tool

    add_tool(get_user_info)
    add_tool(create_draft)
    add_tool(send_draft)
    add_tool(list_drafts)
    add_tool(delete_draft)
    add_tool(list_emails)
    add_tool(get_email)
    add_tool(mark_as_read)
    add_tool(mark_as_unread)

    return mcp


def create_default_server():
    raise RuntimeError(
        "Stdio mode has been removed. Use remote.py for the production server."
    )


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _ensure_session():
    session = get_authenticated_session()
    if session is None:
        raise ValueError(
            "Gmail session not available. The server is not connected to Gmail."
        )
    return session


async def get_user_info() -> dict:
    """Get the current Gmail user's profile information.

    Returns the authenticated user's email address, total messages,
    and total threads. Useful as a connectivity check.
    """
    session = _ensure_session()
    return session.get_user_info()


async def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    html_body: str | None = None,
) -> dict:
    """Create a draft email in Gmail.

    The draft is saved but NOT sent. The user must review and send the
    draft manually, or call send_draft to send programmatically.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body
        cc: Optional CC recipient
        bcc: Optional BCC recipient
        html_body: Optional HTML body (overrides plain text)
    """
    session = _ensure_session()
    return session.create_draft(
        to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
    )


async def send_draft(draft_id: str) -> dict:
    """Send an existing draft by its ID.

    Args:
        draft_id: The Gmail draft ID to send
    """
    session = _ensure_session()
    return session.send_draft(draft_id)


async def list_drafts(max_results: int = 10) -> list[dict]:
    """List email drafts in the authenticated user's account.

    Args:
        max_results: Maximum number of drafts to return (default 10)
    """
    session = _ensure_session()
    return session.list_drafts(max_results)


async def delete_draft(draft_id: str) -> bool:
    """Delete a draft by its ID.

    Args:
        draft_id: The Gmail draft ID to delete
    """
    session = _ensure_session()
    return session.delete_draft(draft_id)


async def list_emails(
    query: str = "",
    label_ids: list[str] | None = None,
    max_results: int = 20,
    include_spam_trash: bool = False,
    page_token: str | None = None,
) -> list[dict]:
    """List emails matching query and label filters.

    Uses Gmail's native search syntax for the query parameter.
    Examples:
      - 'is:unread' — all unread emails
      - 'is:unread in:inbox' — unread inbox emails
      - 'from:alice@example.com' — emails from a specific sender
      - 'newer_than:7d' — emails from the last 7 days

    Returns a list of email summaries (id, thread_id, subject, from, to,
    snippet, date, labels).

    Args:
        query: Gmail search query string (optional)
        label_ids: Filter by Gmail label IDs (optional)
        max_results: Maximum results to return (default 20)
        include_spam_trash: Include spam and trash folders (default False)
        page_token: Token for pagination (optional)
    """
    session = _ensure_session()
    return session.list_emails(
        query=query,
        label_ids=label_ids,
        max_results=max_results,
        include_spam_trash=include_spam_trash,
        page_token=page_token,
    )


async def get_email(email_id: str) -> dict:
    """Get full content of a single email by its ID.

    Returns the email with all headers (from, to, cc, bcc), body text,
    body HTML, and a list of attachment metadata (filename, mime_type).

    Args:
        email_id: The Gmail message ID
    """
    session = _ensure_session()
    return session.get_email(email_id)


async def mark_as_read(email_id: str) -> bool:
    """Mark an email as read by removing the UNREAD label.

    Args:
        email_id: The Gmail message ID
    """
    session = _ensure_session()
    return session.mark_as_read(email_id)


async def mark_as_unread(email_id: str) -> bool:
    """Mark an email as unread by adding the UNREAD label.

    Args:
        email_id: The Gmail message ID
    """
    session = _ensure_session()
    return session.mark_as_unread(email_id)


# ---------------------------------------------------------------------------
# Internal FastMCP instance (used for signature introspection only)
# ---------------------------------------------------------------------------

_internal_mcp = FastMCP("_internal")


@_internal_mcp.tool()
async def _internal_tool():
    pass
