from django.db import models
from django.db.models import Q

from common.models.abstracts import BaseModel


class DiscordChannelPurpose(models.TextChoices):
    BOARD_UPDATES = "BOARD_UPDATES", "Board updates"


class DiscordChannel(BaseModel):
    webhook_url = models.URLField(
        verbose_name="Webhook URL",
        max_length=2048,
    )
    purpose = models.CharField(
        verbose_name="Purpose",
        max_length=64,
        choices=DiscordChannelPurpose.choices,
    )
    name = models.CharField(
        verbose_name="Name",
        max_length=120,
    )
    is_active = models.BooleanField(
        verbose_name="Is active",
        default=True,
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Discord channel"
        verbose_name_plural = "Discord channels"
        indexes = [
            models.Index(fields=["purpose"], name="comm_discord_purpose_idx"),
            models.Index(fields=["is_active"], name="comm_discord_active_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["purpose"],
                condition=Q(is_active=True),
                name="comm_discord_unique_active_purpose",
            ),
        ]

    @classmethod
    def get_active_webhook_url_by_purpose(cls, purpose: str) -> str | None:
        channel = (
            cls.objects.filter(purpose=purpose, is_active=True)
            .order_by("-updated_at")
            .values("webhook_url")
            .first()
        )
        if channel is None:
            return None
        return channel["webhook_url"]

    def __str__(self) -> str:
        return f"{self.name} ({self.purpose})"
