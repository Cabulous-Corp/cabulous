from django.conf import settings
from django.db import models

from common.models.abstracts import BaseModel


class Photo(BaseModel):
    object_key = models.CharField(max_length=1024, unique=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_photos",
    )
    taken_on = models.DateField()
    caption = models.TextField(blank=True, default="")
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()

    class Meta(BaseModel.Meta):
        ordering = ["-taken_on", "-created_at", "-id"]
        indexes = [
            models.Index(fields=["taken_on", "id"], name="media_photo_taken_idx"),
            models.Index(fields=["uploader", "taken_on"], name="media_photo_user_idx"),
        ]
