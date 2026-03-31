from typing import Any

from celery import shared_task
from pydantic import HttpUrl

from communication.models import DiscordChannelPurpose
from communication.models.discord_message import (
    DiscordEmbedAuthor,
    DiscordEmbedField,
    DiscordEmbedFooter,
    DiscordEmbedImage,
    DiscordEmbedThumbnail,
)
from communication.services import DiscordService, EmailService


def _parse_http_url(url: HttpUrl | str | None) -> HttpUrl | None:
    if url is None:
        return None
    if isinstance(url, HttpUrl):
        return url
    return HttpUrl(url)


def _parse_embed_footer(
    footer: DiscordEmbedFooter | dict[str, Any] | None,
) -> DiscordEmbedFooter | None:
    if footer is None:
        return None
    if isinstance(footer, DiscordEmbedFooter):
        return footer
    return DiscordEmbedFooter.model_validate(footer)


def _parse_embed_image(
    image: DiscordEmbedImage | dict[str, Any] | None,
) -> DiscordEmbedImage | None:
    if image is None:
        return None
    if isinstance(image, DiscordEmbedImage):
        return image
    return DiscordEmbedImage.model_validate(image)


def _parse_embed_thumbnail(
    thumbnail: DiscordEmbedThumbnail | dict[str, Any] | None,
) -> DiscordEmbedThumbnail | None:
    if thumbnail is None:
        return None
    if isinstance(thumbnail, DiscordEmbedThumbnail):
        return thumbnail
    return DiscordEmbedThumbnail.model_validate(thumbnail)


def _parse_embed_author(
    author: DiscordEmbedAuthor | dict[str, Any] | None,
) -> DiscordEmbedAuthor | None:
    if author is None:
        return None
    if isinstance(author, DiscordEmbedAuthor):
        return author
    return DiscordEmbedAuthor.model_validate(author)


def _parse_embed_fields(
    fields: list[DiscordEmbedField | dict[str, Any]] | None,
) -> list[DiscordEmbedField] | None:
    if fields is None:
        return None
    parsed_fields: list[DiscordEmbedField] = []
    for field in fields:
        if isinstance(field, DiscordEmbedField):
            parsed_fields.append(field)
        else:
            parsed_fields.append(DiscordEmbedField.model_validate(field))
    return parsed_fields


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
    title: str | None = None,
    description: str | None = None,
    color: int | None = None,
    url: HttpUrl | str | None = None,
    timestamp: str | None = None,
    footer: DiscordEmbedFooter | dict[str, Any] | None = None,
    image: DiscordEmbedImage | dict[str, Any] | None = None,
    thumbnail: DiscordEmbedThumbnail | dict[str, Any] | None = None,
    author: DiscordEmbedAuthor | dict[str, Any] | None = None,
    fields: list[DiscordEmbedField | dict[str, Any]] | None = None,
    content: str | None = None,
) -> None:
    DiscordService.send_channel_embed(
        webhook_url=webhook_url,
        title=title,
        description=description,
        color=color,
        url=_parse_http_url(url),
        timestamp=timestamp,
        footer=_parse_embed_footer(footer),
        image=_parse_embed_image(image),
        thumbnail=_parse_embed_thumbnail(thumbnail),
        author=_parse_embed_author(author),
        fields=_parse_embed_fields(fields),
        content=content,
    )


@shared_task(name="communication.send_discord_embed_by_purpose")
def send_discord_channel_embed_by_purpose_task(
    *,
    purpose: DiscordChannelPurpose | str,
    title: str | None = None,
    description: str | None = None,
    color: int | None = None,
    url: HttpUrl | str | None = None,
    timestamp: str | None = None,
    footer: DiscordEmbedFooter | dict[str, Any] | None = None,
    image: DiscordEmbedImage | dict[str, Any] | None = None,
    thumbnail: DiscordEmbedThumbnail | dict[str, Any] | None = None,
    author: DiscordEmbedAuthor | dict[str, Any] | None = None,
    fields: list[DiscordEmbedField | dict[str, Any]] | None = None,
    content: str | None = None,
) -> None:
    DiscordService.send_channel_embed_by_purpose(
        purpose=purpose,
        title=title,
        description=description,
        color=color,
        url=_parse_http_url(url),
        timestamp=timestamp,
        footer=_parse_embed_footer(footer),
        image=_parse_embed_image(image),
        thumbnail=_parse_embed_thumbnail(thumbnail),
        author=_parse_embed_author(author),
        fields=_parse_embed_fields(fields),
        content=content,
    )
