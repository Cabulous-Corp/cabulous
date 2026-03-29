from pathlib import PurePosixPath
from typing import Any

import requests
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from pydantic import HttpUrl

from communication.models.discord import (
    DiscordEmbed,
    DiscordEmbedAuthor,
    DiscordEmbedField,
    DiscordEmbedFooter,
    DiscordEmbedImage,
    DiscordEmbedThumbnail,
    DiscordWebhookPayload,
)


class DiscordService:
    """
    Service responsible for sending Discord webhook messages.

    Methods:
    - send_channel_message(webhook_url, content)
    - send_channel_message_from_template(webhook_url, template_path, context=None)
    - send_channel_embed(webhook_url, ...)
    """

    MESSAGE_TEMPLATE_EXTENSIONS = ("txt", "md")
    MESSAGE_TEMPLATE_BASE_DIR = PurePosixPath("discord/messages")

    @staticmethod
    def _send_webhook_payload(payload: dict[str, Any], webhook_url: str = "") -> None:
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}") from e

    @staticmethod
    def send_channel_message(webhook_url: str, content: str) -> None:
        """
        Send a plain channel message to a Discord webhook.

        Args:
            webhook_url: Discord webhook URL.
            content: Raw message content (Discord markdown is supported).
        """
        payload = {"content": content}
        DiscordService._send_webhook_payload(payload, webhook_url)

    @staticmethod
    def send_channel_message_from_template(
        webhook_url: str,
        template_path: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Render and send a channel message from a template under discord/messages.

        Args:
            webhook_url: Discord webhook URL.
            template_path:
                Template identifier.
                - With extension (.txt/.md): exact file resolution.
                  Examples: 'test_message.md', 'auth/onboarding/test_message.txt'
                - Without extension: fallback lookup tries .txt then .md.
                  Example: 'test_message'
            context: Template context dictionary.
        """
        content = DiscordService._render_channel_message_template(template_path, context)
        DiscordService.send_channel_message(webhook_url=webhook_url, content=content)

    @staticmethod
    def _render_channel_message_template(
        template_path: str, context: dict[str, Any] | None = None
    ) -> str:
        normalized_template_name = template_path.strip().lstrip("/")
        template_path = PurePosixPath(normalized_template_name)

        if template_path.suffix in {".txt", ".md"}:
            if str(template_path).startswith(f"{DiscordService.MESSAGE_TEMPLATE_BASE_DIR}/"):
                template_candidates = [str(template_path)]
            else:
                template_candidates = [
                    str(DiscordService.MESSAGE_TEMPLATE_BASE_DIR / template_path)
                ]
        else:
            if str(template_path).startswith(f"{DiscordService.MESSAGE_TEMPLATE_BASE_DIR}/"):
                base_template = template_path
            else:
                base_template = DiscordService.MESSAGE_TEMPLATE_BASE_DIR / template_path
            template_candidates = [
                f"{base_template}.{extension}"
                for extension in DiscordService.MESSAGE_TEMPLATE_EXTENSIONS
            ]

        try:
            content = render_to_string(template_candidates, context or {})
        except TemplateDoesNotExist as exc:
            raise ValueError(
                f"Discord message template '{template_path}' not found. "
                "Use a template name under 'discord/messages/' and provide the full filename "
                "when you want an exact file (for example: 'test_message.md' or "
                "'auth/onboarding/test_message.md')."
            ) from exc
        return content.strip()

    @staticmethod
    def send_channel_embed(
        webhook_url: str,
        title: str | None = None,
        description: str | None = None,
        color: int | None = None,
        url: HttpUrl | None = None,
        timestamp: str | None = None,
        footer: DiscordEmbedFooter | None = None,
        image: DiscordEmbedImage | None = None,
        thumbnail: DiscordEmbedThumbnail | None = None,
        author: DiscordEmbedAuthor | None = None,
        fields: list[DiscordEmbedField] | None = None,
        content: str | None = None,
    ) -> None:
        """
        Service para envio de mensagens e embeds para webhooks do Discord.

        Os schemas Pydantic utilizados (Embed, Fields, Footer, Author, Image, etc.)
        estão definidos em:
        communication/models/discord.py

        Exemplo de uso:

        from services.discord import DiscordService
        from communication.models.discord import (
            DiscordEmbedField,
            DiscordEmbedFooter,
            DiscordEmbedAuthor,
            DiscordEmbedImage,
            DiscordEmbedThumbnail,
        )

        DiscordService.send_channel_embed(
            webhook_url="https://discord.com/api/webhooks/...",
            title="Novo evento",
            description="Evento criado com sucesso",
            color=5814783,
            url="https://mcoder.com.br",
            timestamp="2026-03-26T12:00:00Z",
            content="Mensagem opcional fora do embed",
            footer=DiscordEmbedFooter(
                text="Sistema mCoder",
                icon_url="https://example.com/icon.png",
            ),
            author=DiscordEmbedAuthor(
                name="mCoder Bot",
                url="https://mcoder.com.br",
                icon_url="https://example.com/bot.png",
            ),
            image=DiscordEmbedImage(
                url="https://example.com/image.png",
            ),
            thumbnail=DiscordEmbedThumbnail(
                url="https://example.com/thumb.png",
            ),
            fields=[
                DiscordEmbedField(
                    name="Usuário",
                    value="Marcos",
                    inline=True,
                ),
                DiscordEmbedField(
                    name="Plano",
                    value="Pro",
                    inline=True,
                ),
            ],
        )
        """

        embed = DiscordEmbed(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=timestamp,
            footer=footer,
            image=image,
            thumbnail=thumbnail,
            author=author,
            fields=fields,
        )

        payload = DiscordWebhookPayload(
            content=content,
            embeds=[embed],
        )

        DiscordService._send_webhook_payload(
            payload.model_dump(exclude_none=True),
            webhook_url,
        )
