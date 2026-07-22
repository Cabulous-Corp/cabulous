import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from common.models.abstracts import AbstractSoftDeleteModel, BaseModel, SoftDeleteQuerySet

from .constants import EVENT_TYPE_COLOR_MAP
from .enums import Audience, EventStatus, EventType


# Kept for migration 0001_initial.py compatibility (references this function).
def event_thumbnail_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    title = getattr(instance, "title", "event")
    name = slugify(title) or "event"
    return f"events/thumbnails/{name}-{uuid.uuid4().hex}{suffix}"


# ---------------------------------------------------------------------------
# Managers
# ---------------------------------------------------------------------------


class EventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllEventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class Event(AbstractSoftDeleteModel, BaseModel):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_events",
        verbose_name="Criador",
    )
    title = models.CharField(max_length=255, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")
    start_at = models.DateTimeField(verbose_name="Início do evento")
    end_at = models.DateTimeField(verbose_name="Fim do evento")
    type = models.CharField(choices=EventType.choices, max_length=30, verbose_name="Tipo")
    status = models.CharField(
        choices=EventStatus.choices, max_length=20, verbose_name="Status"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelado em")

    objects = EventManager()
    all_objects = AllEventManager()

    @property
    def type_color(self) -> str:
        try:
            event_type = EventType(self.type)
            return EVENT_TYPE_COLOR_MAP.get(event_type, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    class Meta(BaseModel.Meta):
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["type", "start_at"], name="events_type_start_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gte=models.F("start_at")),
                name="events_end_gte_start",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.end_at and self.end_at < self.start_at:
            raise ValidationError(
                {"end_at": "A data de término não pode ser anterior à data de início."}
            )


class EventAudience(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="audiences",
    )
    audience = models.CharField(
        choices=Audience.choices, max_length=30, verbose_name="Público-alvo"
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Público do evento"
        verbose_name_plural = "Públicos do evento"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "audience"], name="events_audience_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event} - {self.audience}"


class EventParticipant(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_participations",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="events_participant_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.event}"


class EventLocation(BaseModel):
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="location",
    )
    name = models.CharField(max_length=255, blank=True, verbose_name="Nome do local")
    address = models.TextField(verbose_name="Endereço")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta(BaseModel.Meta):
        verbose_name = "Local do evento"
        verbose_name_plural = "Locais do evento"

    def __str__(self) -> str:
        return self.name or self.address


class EventPhoto(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    photo = models.ForeignKey(
        "media.Photo",
        on_delete=models.CASCADE,
        related_name="event_photos",
    )
    is_thumbnail = models.BooleanField(default=False, verbose_name="É thumbnail")
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_event_photos",
        verbose_name="Vinculado por",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Foto do evento"
        verbose_name_plural = "Fotos do evento"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "photo"], name="events_photo_unique"
            ),
            models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(is_thumbnail=True),
                name="events_one_thumbnail",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event} - {self.photo}"


class Highlight(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="highlights",
    )
    text = models.CharField(max_length=500, verbose_name="Texto")

    class Meta(BaseModel.Meta):
        verbose_name = "Destaque"
        verbose_name_plural = "Destaques"

    def __str__(self) -> str:
        return self.text[:50]


class HighlightPhoto(BaseModel):
    highlight = models.ForeignKey(
        Highlight,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    photo = models.ForeignKey(
        "media.Photo",
        on_delete=models.CASCADE,
        related_name="highlight_photos",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Foto do destaque"
        verbose_name_plural = "Fotos do destaque"

    def __str__(self) -> str:
        return f"{self.highlight} - {self.photo}"
