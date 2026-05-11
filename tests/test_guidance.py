"""Tests for guidance prompts, resources, and tools."""

import pytest

from src.guidance.prompts import (
    professional_email_composer,
    follow_up_email_generator,
    meeting_request_composer,
    draft_strategy_advisor,
    email_review_checklist,
)
from src.guidance.resources import (
    get_html_template,
    get_signature_resource,
    get_security_resource,
    get_etiquette_resource,
)
from src.guidance.tools import (
    get_subject_line_help,
    validate_subject_line_tool,
    get_email_templates,
)

# Prompt tests


class TestProfessionalEmailComposer:
    def test_returns_professional_email_composition_guide(self):
        result = professional_email_composer()
        assert "Professional Email Composition Guide" in result

    def test_includes_email_type(self):
        result = professional_email_composer(email_type="meeting")
        assert "Email Type: Meeting" in result

    def test_includes_recipient_relationship(self):
        result = professional_email_composer(recipient_relationship="executive")
        assert "Recipient Relationship: Executive" in result

    def test_includes_urgency(self):
        result = professional_email_composer(urgency="urgent")
        assert "Urgency: Urgent" in result

    def test_includes_meeting_structure_for_meeting_type(self):
        result = professional_email_composer(email_type="meeting")
        assert "Meeting Request Structure" in result


class TestFollowUpEmailGenerator:
    def test_returns_polite_reminder_by_default(self):
        result = follow_up_email_generator("test project")
        assert "Polite Follow-Up Email" in result
        assert "test project" in result

    def test_returns_status_check_when_requested(self):
        result = follow_up_email_generator(
            "test project", follow_up_type="status_check"
        )
        assert "Status Check Follow-Up" in result

    def test_includes_time_since_last(self):
        result = follow_up_email_generator("test project", time_since_last="3 days")
        assert "3 days" in result


class TestMeetingRequestComposer:
    def test_returns_discussion_template_by_default(self):
        result = meeting_request_composer("Q4 planning")
        assert "Discussion Meeting Request" in result
        assert "Q4 planning" in result

    def test_returns_decision_template_when_requested(self):
        result = meeting_request_composer("Q4 planning", meeting_type="decision")
        assert "Decision-Making Meeting" in result

    def test_includes_duration_and_attendees(self):
        result = meeting_request_composer(
            "Q4 planning", duration_minutes=60, attendee_count=5
        )
        assert "60 minutes" in result
        assert "5 people" in result


class TestDraftStrategyAdvisor:
    def test_returns_recommendation(self):
        result = draft_strategy_advisor("routine update")
        assert "Draft Strategy Recommendation" in result

    def test_recommends_draft_for_high_risk(self):
        result = draft_strategy_advisor("sensitive legal matter")
        assert "Save as Draft" in result

    def test_recommends_send_for_urgent_simple(self):
        result = draft_strategy_advisor(
            "quick question", urgency="urgent", complexity="simple"
        )
        assert "Send Immediately" in result

    def test_includes_checklist(self):
        result = draft_strategy_advisor("routine update")
        assert "Pre-Send Checklist" in result
        assert "Subject line clearly describes the content" in result


class TestEmailReviewChecklist:
    def test_returns_checklist(self):
        result = email_review_checklist()
        assert "Email Review Checklist" in result

    def test_includes_attachment_items_when_has_attachments(self):
        result = email_review_checklist(has_attachments=True)
        assert "Attachments" in result
        assert "All referenced attachments are attached" in result

    def test_includes_meeting_items_for_meeting_request(self):
        result = email_review_checklist(email_type="meeting_request")
        assert "Meeting-Specific" in result

    def test_includes_external_items_for_external_recipients(self):
        result = email_review_checklist(recipient_type="external")
        assert "External Recipients" in result


# Resource tests


class TestGetHtmlTemplate:
    def test_returns_known_template(self):
        result = get_html_template("professional_announcement")
        assert "Professional Announcement" in result

    def test_raises_value_error_for_invalid_template(self):
        with pytest.raises(ValueError, match="Template 'invalid' not found"):
            get_html_template("invalid")


class TestGetSignatureResource:
    def test_returns_known_signature(self):
        result = get_signature_resource("standard_professional")
        assert result  # Non-empty string

    def test_returns_default_for_invalid_signature(self):
        """get_signature_template falls back to standard_professional for unknown types."""
        result = get_signature_resource("invalid")
        assert result  # Returns default signature, no error


class TestGetSecurityResource:
    def test_returns_known_category(self):
        result = get_security_resource("phishing_prevention")
        assert isinstance(result, dict)
        assert result  # Non-empty dict

    def test_raises_value_error_for_invalid_category(self):
        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            get_security_resource("invalid")


class TestGetEtiquetteResource:
    def test_returns_known_category(self):
        result = get_etiquette_resource("tone_and_language")
        assert isinstance(result, dict)
        assert result  # Non-empty dict

    def test_raises_value_error_for_invalid_category(self):
        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            get_etiquette_resource("invalid")


# Tool tests


class TestGetSubjectLineHelp:
    @pytest.mark.asyncio
    async def test_returns_suggestions(self):
        result = await get_subject_line_help("action_required")
        assert isinstance(result, dict)
        assert result  # Non-empty dict


class TestValidateSubjectLineTool:
    @pytest.mark.asyncio
    async def test_returns_validation(self):
        result = await validate_subject_line_tool("Meeting tomorrow at 3pm")
        assert isinstance(result, dict)
        assert result  # Non-empty dict


class TestGetEmailTemplates:
    @pytest.mark.asyncio
    async def test_returns_html_templates(self):
        result = await get_email_templates("html")
        assert result["template_type"] == "html"
        assert isinstance(result["available_templates"], dict)
        assert result["available_templates"]  # Non-empty dict

    @pytest.mark.asyncio
    async def test_returns_signature_templates(self):
        result = await get_email_templates("signature")
        assert result["template_type"] == "signature"
        assert isinstance(result["available_templates"], dict)
        assert result["available_templates"]  # Non-empty dict

    @pytest.mark.asyncio
    async def test_raises_exception_for_invalid_type(self):
        with pytest.raises(Exception, match="Unknown template type: invalid"):
            await get_email_templates("invalid")


# Integration: verify no token_store or Google SDK imports


class TestNoHeavyDependencies:
    def test_guidance_prompts_has_no_token_store_import(self):
        import src.guidance.prompts as prompts_module

        assert "token_store" not in dir(prompts_module)

    def test_guidance_resources_has_no_token_store_import(self):
        import src.guidance.resources as resources_module

        assert "token_store" not in dir(resources_module)

    def test_guidance_tools_has_no_token_store_import(self):
        import src.guidance.tools as tools_module

        assert "token_store" not in dir(tools_module)
