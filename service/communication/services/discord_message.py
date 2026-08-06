import requests

from communication.helpers import DiscordChannelHelper
from communication.models import DiscordChannelPurpose
from communication.models.discord_message import DiscordEmbed, DiscordWebhookPayload


class DiscordService:
    """
    Service responsible for sending Discord webhook messages.

    Methods:
    - send_channel_message(webhook_url, content)
    - send_channel_message_by_purpose(purpose, content)
    - send_channel_embed(webhook_url, content=None, embeds=None)
    - send_channel_embed_by_purpose(purpose, content=None, embeds=None)
    """

    @staticmethod
    def _send_webhook_payload(payload: dict[str, object], webhook_url: str = "") -> None:
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}") from e

    @staticmethod
    def send_channel_message(webhook_url: str, content: str) -> None:
        """Send a plain channel message to a Discord webhook."""
        DiscordService._send_webhook_payload({"content": content}, webhook_url)

    @staticmethod
    def send_channel_message_by_purpose(
        purpose: DiscordChannelPurpose | str,
        content: str,
    ) -> None:
        webhook_url = DiscordChannelHelper.get_webhook_url_by_purpose(purpose)
        DiscordService.send_channel_message(webhook_url=webhook_url, content=content)

    @staticmethod
    def send_channel_embed(
        webhook_url: str,
        *,
        content: str | None = None,
        embeds: list[DiscordEmbed] | None = None,
    ) -> None:
        payload = DiscordWebhookPayload(
            content=content,
            embeds=embeds or [],
        )
        DiscordService._send_webhook_payload(
            payload.model_dump(mode="json", exclude_none=True),
            webhook_url,
        )

    @staticmethod
    def send_channel_embed_by_purpose(
        purpose: DiscordChannelPurpose | str,
        *,
        content: str | None = None,
        embeds: list[DiscordEmbed] | None = None,
    ) -> None:
        webhook_url = DiscordChannelHelper.get_webhook_url_by_purpose(purpose)
        DiscordService.send_channel_embed(
            webhook_url=webhook_url,
            content=content,
            embeds=embeds,
        )
