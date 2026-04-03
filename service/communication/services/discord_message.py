from pathlib import PurePosixPath
from typing import Any

import requests
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from communication.helpers import DiscordChannelHelper
from communication.models import DiscordChannelPurpose
from communication.models.discord_message import DiscordEmbed, DiscordWebhookPayload


class DiscordService:
    """
    Service responsible for sending Discord webhook messages.

    Methods:
    - send_channel_message(webhook_url, content)
    - send_channel_message_by_purpose(purpose, content)
    - send_channel_message_from_template(webhook_url, template_path, context=None)
    - send_channel_message_from_template_by_purpose(purpose, template_path, context=None)
    - send_channel_embed(webhook_url, content=None, embeds=None)
    - send_channel_embed_by_purpose(purpose, content=None, embeds=None)
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
    def send_channel_message_by_purpose(
        purpose: DiscordChannelPurpose | str,
        content: str,
    ) -> None:
        webhook_url = DiscordChannelHelper.get_webhook_url_by_purpose(purpose)
        DiscordService.send_channel_message(webhook_url=webhook_url, content=content)

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
    def send_channel_message_from_template_by_purpose(
        purpose: DiscordChannelPurpose | str,
        template_path: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        webhook_url = DiscordChannelHelper.get_webhook_url_by_purpose(purpose)
        DiscordService.send_channel_message_from_template(
            webhook_url=webhook_url,
            template_path=template_path,
            context=context,
        )

    @staticmethod
    def _render_channel_message_template(
        template_path: str, context: dict[str, Any] | None = None
    ) -> str:
        normalized_template_name = template_path.strip().lstrip("/")
        template_path_obj = PurePosixPath(normalized_template_name)

        if template_path_obj.suffix in {".txt", ".md"}:
            if str(template_path_obj).startswith(f"{DiscordService.MESSAGE_TEMPLATE_BASE_DIR}/"):
                template_candidates = [str(template_path_obj)]
            else:
                template_candidates = [
                    str(DiscordService.MESSAGE_TEMPLATE_BASE_DIR / template_path_obj)
                ]
        else:
            if str(template_path_obj).startswith(f"{DiscordService.MESSAGE_TEMPLATE_BASE_DIR}/"):
                base_template = template_path_obj
            else:
                base_template = DiscordService.MESSAGE_TEMPLATE_BASE_DIR / template_path_obj
            template_candidates = [
                f"{base_template}.{extension}"
                for extension in DiscordService.MESSAGE_TEMPLATE_EXTENSIONS
            ]

        try:
            content = render_to_string(template_candidates, context or {})
        except TemplateDoesNotExist as exc:
            raise ValueError(
                f"Discord message template '{normalized_template_name}' not found. "
                "Use a template name under 'discord/messages/' and provide the full filename "
                "when you want an exact file (for example: 'test_message.md' or "
                "'auth/onboarding/test_message.md')."
            ) from exc
        return content.strip()

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
            payload.model_dump(exclude_none=True),
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
