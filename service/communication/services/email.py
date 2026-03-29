from collections.abc import Sequence
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """
    Reusable email service for system-wide email delivery.

    Main methods:
    - send_simple_email(subject, recipients, body, ...)
    - send_html_template_email(subject, recipients, template_path, context=None, ...)
    """

    @staticmethod
    def send_simple_email(
        *,
        subject: str,
        recipients: Sequence[str],
        body: str,
        from_email: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: Sequence[str] | None = None,
        fail_silently: bool = False,
    ) -> int:
        """
        Send a plain-text email.
        """
        to = EmailService._normalize_recipients(recipients, field_name="recipients")
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=to,
            cc=EmailService._normalize_recipients(cc, field_name="cc"),
            bcc=EmailService._normalize_recipients(bcc, field_name="bcc"),
            reply_to=EmailService._normalize_recipients(reply_to, field_name="reply_to"),
        )
        return email.send(fail_silently=fail_silently)

    @staticmethod
    def send_html_template_email(
        *,
        subject: str,
        recipients: Sequence[str],
        template_path: str,
        context: dict[str, Any] | None = None,
        text_body: str | None = None,
        from_email: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: Sequence[str] | None = None,
        fail_silently: bool = False,
    ) -> int:
        """
        Send an email rendered from an HTML template.
        """
        to = EmailService._normalize_recipients(recipients, field_name="recipients")
        html_body = render_to_string(template_path, context or {})
        plain_body = text_body if text_body is not None else strip_tags(html_body).strip()
        if not plain_body:
            plain_body = "This message contains HTML content."

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=to,
            cc=EmailService._normalize_recipients(cc, field_name="cc"),
            bcc=EmailService._normalize_recipients(bcc, field_name="bcc"),
            reply_to=EmailService._normalize_recipients(reply_to, field_name="reply_to"),
        )
        email.attach_alternative(html_body, "text/html")
        return email.send(fail_silently=fail_silently)

    @staticmethod
    def _normalize_recipients(
        recipients: Sequence[str] | None,
        *,
        field_name: str,
    ) -> list[str]:
        if recipients is None:
            return []
        cleaned = [recipient.strip() for recipient in recipients if recipient and recipient.strip()]
        if field_name == "recipients" and not cleaned:
            raise ValueError("At least one recipient is required.")
        return cleaned
