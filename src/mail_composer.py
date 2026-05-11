"""Mail composition for Gmail MCP server."""

import base64
from email.message import EmailMessage

from .models import EmailRequest


class MailComposer:
    """Compose MIME messages from email requests."""

    def compose(self, request: EmailRequest, sender: str) -> str:
        """Build a raw MIME message and return it as a base64url-encoded string.

        Args:
            request: The email request with recipients, subject, and body.
            sender: The sender's email address.

        Returns:
            A base64url-encoded raw message string suitable for the Gmail API.
        """
        message = EmailMessage()

        message["To"] = request.to
        if request.cc:
            message["Cc"] = request.cc
        if request.bcc:
            message["Bcc"] = request.bcc

        message["Subject"] = request.subject
        message["From"] = sender

        if request.html_body:
            message.set_content(request.body)
            message.add_alternative(request.html_body, subtype="html")
        else:
            message.set_content(request.body)

        raw_bytes = base64.urlsafe_b64encode(message.as_bytes())
        return raw_bytes.decode("utf-8")
