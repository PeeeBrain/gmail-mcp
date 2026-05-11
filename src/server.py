"""MCP server implementation for Gmail functionality."""

from typing import Optional, List
from fastmcp import FastMCP

from .gmail_session import GmailSession, GmailSessionFactory
from .token_store import GmailTokenStore
from .models import EmailRequest, EmailResponse, DraftInfo, UserInfo
from .guidance import (
    register_guidance_prompts,
    register_guidance_resources,
    register_guidance_tools,
)

# Module-level session factory set by create_server()
_session_factory: GmailSessionFactory | None = None

# Dummy MCP instance used only for decorators (no runtime use)
_mcp = FastMCP("_internal")


def get_authenticated_session() -> Optional[GmailSession]:
    """Get authenticated Gmail session for current user."""
    if _session_factory is None:
        return None
    return _session_factory.create_current_session()


# Operational tools


@_mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html_body: Optional[str] = None,
    ctx=None,
) -> EmailResponse:
    """Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        html_body: HTML version of email body (optional)
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authenticated user. Please login first with: gmail-mcp --login"
        )

    if ctx:
        await ctx.info(f"Sending email to {to}")

    try:
        # Validate email request
        email_req = EmailRequest(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
        )

        result = session.send_email(
            to=email_req.to,
            subject=email_req.subject,
            body=email_req.body,
            cc=email_req.cc,
            bcc=email_req.bcc,
            html_body=email_req.html_body,
        )

        if ctx:
            await ctx.info(f"Email sent successfully with ID: {result['id']}")

        return EmailResponse(**result)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to send email: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")


@_mcp.tool()
async def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html_body: Optional[str] = None,
    ctx=None,
) -> EmailResponse:
    """Create an email draft.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        html_body: HTML version of email body (optional)
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authenticated user. Please login first with: gmail-mcp --login"
        )

    if ctx:
        await ctx.info(f"Creating draft for {to}")

    try:
        draft_req = EmailRequest(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, html_body=html_body
        )

        result = session.create_draft(
            to=draft_req.to,
            subject=draft_req.subject,
            body=draft_req.body,
            cc=draft_req.cc,
            bcc=draft_req.bcc,
            html_body=draft_req.html_body,
        )

        if ctx:
            await ctx.info(f"Draft created with ID: {result['id']}")

        return EmailResponse(**result)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to create draft: {str(e)}")
        raise Exception(f"Failed to create draft: {str(e)}")


@_mcp.tool()
async def send_draft(draft_id: str, ctx=None) -> EmailResponse:
    """Send an existing email draft.

    Args:
        draft_id: ID of the draft to send
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authenticated user. Please login first with: gmail-mcp --login"
        )

    if ctx:
        await ctx.info(f"Sending draft {draft_id}")

    try:
        result = session.send_draft(draft_id)

        if ctx:
            await ctx.info(f"Draft sent with message ID: {result['id']}")

        return EmailResponse(**result)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to send draft: {str(e)}")
        raise Exception(f"Failed to send draft: {str(e)}")


@_mcp.tool()
async def list_drafts(max_results: int = 10, ctx=None) -> List[DraftInfo]:
    """List email drafts.

    Args:
        max_results: Maximum number of drafts to return (default: 10)
    """
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authenticated user. Please login first with: gmail-mcp --login"
        )

    if ctx:
        await ctx.info(f"Listing up to {max_results} drafts")

    try:
        drafts = session.list_drafts(max_results)
        result = [DraftInfo(**draft) for draft in drafts]

        if ctx:
            await ctx.info(f"Found {len(result)} drafts")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list drafts: {str(e)}")
        raise Exception(f"Failed to list drafts: {str(e)}")


@_mcp.tool()
async def get_user_info(ctx=None) -> UserInfo:
    """Get current authenticated user information."""
    session = get_authenticated_session()
    if not session:
        raise Exception(
            "No authenticated user. Please login first with: gmail-mcp --login"
        )

    try:
        user_info = session.get_user_info()
        result = UserInfo(**user_info)

        if ctx:
            await ctx.info(f"Current user: {result.email}")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get user info: {str(e)}")
        raise Exception(f"Failed to get user info: {str(e)}")


# Server assembly


def create_server(session_factory: GmailSessionFactory) -> FastMCP:
    """Create an MCP server wired to the given session factory.

    Importing this module does NOT touch the filesystem.
    """
    global _session_factory
    _session_factory = session_factory

    mcp = FastMCP("Gmail MCP Server")

    # Guidance prompts, resources, and tools
    register_guidance_prompts(mcp)
    register_guidance_resources(mcp)
    register_guidance_tools(mcp)

    # Operational tools
    mcp.add_tool(send_email)
    mcp.add_tool(create_draft)
    mcp.add_tool(send_draft)
    mcp.add_tool(list_drafts)
    mcp.add_tool(get_user_info)

    return mcp


def create_default_server() -> FastMCP:
    """Create an MCP server with the default token store and session factory."""
    token_store = GmailTokenStore()
    session_factory = GmailSessionFactory(token_store)
    return create_server(session_factory)
