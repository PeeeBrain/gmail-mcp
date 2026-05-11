"""Guidance tools for subject lines and template discovery."""

from fastmcp import FastMCP

from ..resources.html_email_templates import HTML_EMAIL_TEMPLATES
from ..resources.email_signatures import EMAIL_SIGNATURES
from ..resources.subject_line_guidelines import (
    get_subject_line_suggestions,
    validate_subject_line,
)

# Dummy MCP instance used only for decorators (no runtime use)
_mcp = FastMCP("_internal")


@_mcp.tool()
async def get_subject_line_help(
    email_type: str = "general", industry: str = None, ctx=None
) -> dict:
    """Get subject line suggestions and best practices.

    Args:
        email_type: Type of email (action_required, meeting_requests, status_updates, etc.)
        industry: Optional industry for specialized templates (sales, marketing, hr, etc.)
    """
    try:
        suggestions = get_subject_line_suggestions(email_type, industry)

        if ctx:
            await ctx.info(
                f"Generated subject line suggestions for {email_type} emails"
            )

        return suggestions

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get subject line help: {str(e)}")
        raise Exception(f"Failed to get subject line help: {str(e)}")


@_mcp.tool()
async def validate_subject_line_tool(subject: str, ctx=None) -> dict:
    """Validate a subject line against best practices.

    Args:
        subject: Subject line to validate
    """
    try:
        validation = validate_subject_line(subject)

        if ctx:
            await ctx.info(f"Validated subject line: '{subject}'")

        return validation

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to validate subject line: {str(e)}")
        raise Exception(f"Failed to validate subject line: {str(e)}")


@_mcp.tool()
async def get_email_templates(template_type: str = "html", ctx=None) -> dict:
    """Get available email templates.

    Args:
        template_type: Type of templates to retrieve (html, signature)
    """
    try:
        if template_type == "html":
            templates = {
                name: "HTML email template" for name in HTML_EMAIL_TEMPLATES.keys()
            }
        elif template_type == "signature":
            templates = {
                name: "Email signature template" for name in EMAIL_SIGNATURES.keys()
            }
        else:
            raise ValueError(
                f"Unknown template type: {template_type}. Use 'html' or 'signature'"
            )

        if ctx:
            await ctx.info(f"Retrieved {len(templates)} {template_type} templates")

        return {
            "template_type": template_type,
            "available_templates": templates,
            "usage": "Use get_html_template() or get_signature_template() to retrieve specific templates",
        }

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get templates: {str(e)}")
        raise Exception(f"Failed to get templates: {str(e)}")


def register_guidance_tools(mcp) -> None:
    """Register all guidance tools on the given MCP server."""
    mcp.add_tool(get_subject_line_help)
    mcp.add_tool(validate_subject_line_tool)
    mcp.add_tool(get_email_templates)
