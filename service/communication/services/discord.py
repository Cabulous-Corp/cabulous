from typing import Any

import requests
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
    @staticmethod
    def _send(payload: dict[str, Any], webhook_url: str = "") -> None:
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}") from e

    @staticmethod
    def send_message(webhook_url: str, content: str) -> None:
        payload = {"content": content}
        DiscordService._send(payload, webhook_url)

    @staticmethod
    def send_embed(
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

        DiscordService.send_embed(
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

        DiscordService._send(
            payload.model_dump(exclude_none=True),
            webhook_url,
        )
