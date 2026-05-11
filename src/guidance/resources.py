"""Guidance resources for email templates, signatures, and guidelines."""

from fastmcp import FastMCP

from ..resources.html_email_templates import HTML_EMAIL_TEMPLATES
from ..resources.email_signatures import get_signature_template
from ..resources.email_security_guidelines import get_security_guidelines_by_category
from ..resources.email_etiquette import EMAIL_ETIQUETTE_GUIDELINES

# Dummy MCP instance used only for decorators (no runtime use)
_mcp = FastMCP("_internal")


@_mcp.resource("template://html_email/{template_name}")
def get_html_template(template_name: str) -> str:
    """Get HTML email template by name.

    Available templates: professional_announcement, meeting_invitation, project_update, newsletter
    """
    template = HTML_EMAIL_TEMPLATES.get(template_name)
    if not template:
        available = list(HTML_EMAIL_TEMPLATES.keys())
        raise ValueError(
            f"Template '{template_name}' not found. Available: {', '.join(available)}"
        )
    return template


@_mcp.resource("template://signature/{signature_type}")
def get_signature_resource(signature_type: str) -> str:
    """Get email signature template by type.

    Available types: standard_professional, detailed_professional, consultant_freelancer,
    sales_business_development, executive_minimal, startup_founder, academic_researcher,
    creative_professional, nonprofit_social_impact, tech_developer, legal_professional,
    healthcare_medical, holiday_seasonal
    """
    return get_signature_template(signature_type)


@_mcp.resource("guidelines://security/{category}")
def get_security_resource(category: str) -> dict:
    """Get email security guidelines by category.

    Available categories: recipient_management, sensitive_information, phishing_prevention,
    attachment_security, compliance_legal, access_control, external_communication
    """
    guidelines = get_security_guidelines_by_category(category)
    if not guidelines:
        available = [
            "recipient_management",
            "sensitive_information",
            "phishing_prevention",
            "attachment_security",
            "compliance_legal",
            "access_control",
            "external_communication",
        ]
        raise ValueError(
            f"Category '{category}' not found. Available: {', '.join(available)}"
        )
    return guidelines


@_mcp.resource("guidelines://etiquette/{category}")
def get_etiquette_resource(category: str) -> dict:
    """Get email etiquette guidelines by category.

    Available categories: tone_and_language, timing_and_response, structure_and_formatting,
    professional_courtesy, cultural_considerations, meeting_email_etiquette
    """
    guidelines = EMAIL_ETIQUETTE_GUIDELINES.get(category)
    if not guidelines:
        available = list(EMAIL_ETIQUETTE_GUIDELINES.keys())
        raise ValueError(
            f"Category '{category}' not found. Available: {', '.join(available)}"
        )
    return guidelines


def register_guidance_resources(mcp) -> None:
    """Register all guidance resources on the given MCP server."""
    mcp.add_resource(get_html_template)
    mcp.add_resource(get_signature_resource)
    mcp.add_resource(get_security_resource)
    mcp.add_resource(get_etiquette_resource)
