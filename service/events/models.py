import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from common.models.abstracts import BaseModel

from .constants import EVENT_TYPE_COLOR_MAP, PUBLIC_COLOR_MAP
from .enums import EventType, Public


def event_thumbnail_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    title = getattr(instance, "title", "event")
    name = slugify(title) or "event"
    return f"events/thumbnails/{name}-{uuid.uuid4().hex}{suffix}"


class Event(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")

    start_at = models.DateTimeField(verbose_name="Início do evento")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="Fim do evento")

    thumbnail = models.ImageField(
        upload_to=event_thumbnail_upload_to, null=True, blank=True, verbose_name="Thumbnail"
    )
    type = models.CharField(choices=EventType.choices, max_length=30, verbose_name="Tipo")
    public = models.CharField(choices=Public.choices, max_length=30, verbose_name="Público")

    @property
    def type_color(self) -> str:
        try:
            event_type = EventType(self.type)
            return EVENT_TYPE_COLOR_MAP.get(event_type, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    @property
    def public_color(self) -> str:
        try:
            public_type = Public(self.public)
            return PUBLIC_COLOR_MAP.get(public_type, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    class Meta(BaseModel.Meta):
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["type", "start_at"]),
            models.Index(fields=["public"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.end_at and self.end_at < self.start_at:
            raise ValidationError(
                {"end_at": "A data de término não pode ser anterior à data de início."}
            )
