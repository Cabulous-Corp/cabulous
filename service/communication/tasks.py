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


@shared_task(name="communication.send_html_template_email")
def send_html_template_email_task(
    *,
    subject: str,
    recipients: list[str],
    template_path: str,
    context: dict[str, Any] | None = None,
) -> int:
    return EmailService.send_html_template_email(
        subject=subject,
        recipients=recipients,
        template_path=template_path,
        context=context,
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
