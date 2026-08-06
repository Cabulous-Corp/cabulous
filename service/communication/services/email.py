from collections.abc import Sequence
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """
    Reusable email service for system-wide email delivery.

    Methods:
    - send_html_template_email(subject, recipients, template_path, context=None)
    """

    @staticmethod
    def send_html_template_email(
        *,
        subject: str,
        recipients: Sequence[str],
        template_path: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Send an email rendered from an HTML template."""
        to = EmailService._normalize_recipients(recipients)
        html_body = render_to_string(template_path, context or {})
        plain_body = strip_tags(html_body).strip() or "This message contains HTML content."

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to,
        )
        email.attach_alternative(html_body, "text/html")
        return email.send(fail_silently=False)

    @staticmethod
    def _normalize_recipients(recipients: Sequence[str]) -> list[str]:
        cleaned = [r.strip() for r in recipients if r and r.strip()]
        if not cleaned:
            raise ValueError("At least one recipient is required.")
        return cleaned
