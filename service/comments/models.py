from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxLengthValidator
from django.db import models

from common.models.abstracts import BaseModel

_MAX_BODY_LEN = 5000


class Comment(BaseModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
    )
    body = models.TextField(
        max_length=_MAX_BODY_LEN,
        validators=[MaxLengthValidator(_MAX_BODY_LEN)],
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.UUIDField()
    target = GenericForeignKey("content_type", "object_id")
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id", "created_at", "id"],
                name="comments_target_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.target} ({self.created_at})"
