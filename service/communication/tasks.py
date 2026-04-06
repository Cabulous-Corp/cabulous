from typing import Any

from celery import shared_task

from communication.models import DiscordChannelPurpose
from communication.models.discord_message import DiscordEmbed
from communication.services import DiscordService, EmailService


def _parse_embeds(
    embeds: list[DiscordEmbed | dict[str, Any]] | None,
) -> list[DiscordEmbed] | None:
    if embeds is None:
        return None

    parsed: list[DiscordEmbed] = []
    for embed in embeds:
        if isinstance(embed, DiscordEmbed):
            parsed.append(embed)
        else:
            parsed.append(DiscordEmbed.model_validate(embed))
    return parsed


@shared_task(name="communication.send_simple_email")
def send_simple_email_task(
    *,
    subject: str,
    recipients: list[str],
    body: str,
    from_email: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
    fail_silently: bool = False,
) -> int:
    return EmailService.send_simple_email(
        subject=subject,
        recipients=recipients,
        body=body,
        from_email=from_email,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        fail_silently=fail_silently,
    )


@shared_task(name="communication.send_html_template_email")
def send_html_template_email_task(
    *,
    subject: str,
    recipients: list[str],
    template_path: str,
    context: dict[str, Any] | None = None,
    text_body: str | None = None,
    from_email: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
    fail_silently: bool = False,
) -> int:
    return EmailService.send_html_template_email(
        subject=subject,
        recipients=recipients,
        template_path=template_path,
        context=context,
        text_body=text_body,
        from_email=from_email,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        fail_silently=fail_silently,
    )


@shared_task(name="communication.send_discord_channel_message")
def send_discord_channel_message_task(*, webhook_url: str, content: str) -> None:
    DiscordService.send_channel_message(webhook_url=webhook_url, content=content)


@shared_task(name="communication.send_discord_channel_message_by_purpose")
def send_discord_channel_message_by_purpose_task(
    *,
    purpose: DiscordChannelPurpose | str,
    content: str,
) -> None:
    DiscordService.send_channel_message_by_purpose(
        purpose=purpose,
        content=content,
    )


@shared_task(name="communication.send_discord_message_from_template")
def send_discord_channel_message_from_template_task(
    *,
    webhook_url: str,
    template_path: str,
    context: dict[str, Any] | None = None,
) -> None:
    DiscordService.send_channel_message_from_template(
        webhook_url=webhook_url,
        template_path=template_path,
        context=context,
    )


@shared_task(name="communication.send_discord_message_from_template_by_purpose")
def send_discord_channel_message_from_template_by_purpose_task(
    *,
    purpose: DiscordChannelPurpose | str,
    template_path: str,
    context: dict[str, Any] | None = None,
) -> None:
    DiscordService.send_channel_message_from_template_by_purpose(
        purpose=purpose,
        template_path=template_path,
        context=context,
    )


@shared_task(name="communication.send_discord_embed")
def send_discord_channel_embed_task(
    *,
    webhook_url: str,
    content: str | None = None,
    embeds: list[DiscordEmbed | dict[str, Any]] | None = None,
) -> None:
    DiscordService.send_channel_embed(
        webhook_url=webhook_url,
        content=content,
        embeds=_parse_embeds(embeds),
    )


@shared_task(name="communication.send_discord_embed_by_purpose")
def send_discord_channel_embed_by_purpose_task(
    *,
    purpose: DiscordChannelPurpose | str,
    content: str | None = None,
    embeds: list[DiscordEmbed | dict[str, Any]] | None = None,
) -> None:
    DiscordService.send_channel_embed_by_purpose(
        purpose=purpose,
        content=content,
        embeds=_parse_embeds(embeds),
    )
