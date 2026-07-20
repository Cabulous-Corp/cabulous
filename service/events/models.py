from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from common.models.abstracts import (
    AbstractSoftDeleteModel,
    BaseModel,
    SoftDeleteQuerySet,
)

from .constants import AUDIENCE_COLOR_MAP, EVENT_STATUS_COLOR_MAP, EVENT_TYPE_COLOR_MAP
from .enums import Audience, EventStatus, EventType


class ActiveEventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllEventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class Event(AbstractSoftDeleteModel, BaseModel):
    title = models.CharField(max_length=255, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")
    start_at = models.DateTimeField(verbose_name="Início do evento")
    end_at = models.DateTimeField(verbose_name="Fim do evento")
    type = models.CharField(choices=EventType.choices, max_length=30, verbose_name="Tipo")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_events",
        verbose_name="Criador",
    )
    status = models.CharField(
        choices=EventStatus.choices,
        max_length=30,
        verbose_name="Status",
    )
    cancelled_at = models.DateTimeField(
        verbose_name="Cancelado em",
        null=True,
        blank=True,
    )

    objects = ActiveEventManager()  # type: ignore[misc]
    all_objects = AllEventManager()  # type: ignore[misc]

    @property
    def type_color(self) -> str:
        try:
            event_type = EventType(self.type)
            return EVENT_TYPE_COLOR_MAP.get(event_type, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    @property
    def status_color(self) -> str:
        try:
            event_status = EventStatus(self.status)
            return EVENT_STATUS_COLOR_MAP.get(event_status, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    class Meta(BaseModel.Meta):
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-start_at", "-created_at", "-id"]
        indexes = [
            models.Index(fields=["type", "start_at"], name="events_type_start_idx"),
            models.Index(fields=["status"], name="events_status_idx"),
            models.Index(fields=["deleted_at", "start_at"], name="events_deleted_start_idx"),
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
        if self.end_at is not None and self.end_at < self.start_at:
            raise ValidationError(
                {"end_at": "A data de término não pode ser anterior à data de início."}
            )


class EventAudience(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="audiences",
        verbose_name="Evento",
    )
    audience = models.CharField(choices=Audience.choices, max_length=30, verbose_name="Público")

    class Meta(BaseModel.Meta):
        verbose_name = "Público do evento"
        verbose_name_plural = "Públicos do evento"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "audience"],
                name="events_audience_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_id} / {self.audience}"

    @property
    def audience_color(self) -> str:
        try:
            audience_value = Audience(self.audience)
            return AUDIENCE_COLOR_MAP.get(audience_value, "#FFFFFF")
        except ValueError:
            return "#FFFFFF"


class EventParticipant(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name="Evento",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_participations",
        verbose_name="Usuário",
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_event_participations",
        verbose_name="Adicionado por",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="events_participant_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_id} / {self.user_id}"


class EventLocation(BaseModel):
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="location",
        verbose_name="Evento",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    street = models.CharField(max_length=255, verbose_name="Logradouro")
    number = models.CharField(max_length=50, verbose_name="Número")
    complement = models.CharField(max_length=255, blank=True, default="", verbose_name="Complemento")
    neighborhood = models.CharField(max_length=255, verbose_name="Bairro")
    city = models.CharField(max_length=255, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="UF")
    postal_code = models.CharField(max_length=20, verbose_name="CEP")
    country = models.CharField(max_length=2, default="BR", verbose_name="País")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Latitude",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        verbose_name="Longitude",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"

    def __str__(self) -> str:
        return f"{self.name} ({self.city}/{self.state})"


class EventPhoto(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_photos",
        verbose_name="Evento",
    )
    photo = models.ForeignKey(
        "media.Photo",
        on_delete=models.CASCADE,
        related_name="event_links",
        verbose_name="Foto",
    )
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="linked_event_photos",
        verbose_name="Vinculado por",
    )
    is_thumbnail = models.BooleanField(default=False, verbose_name="Thumbnail")

    class Meta(BaseModel.Meta):
        verbose_name = "Foto do evento"
        verbose_name_plural = "Fotos do evento"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "photo"],
                name="events_photo_unique",
            ),
            models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(is_thumbnail=True),
                name="events_one_thumbnail",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_id} / {self.photo_id}"


class Highlight(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="highlights",
        verbose_name="Evento",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_highlights",
        verbose_name="Autor",
    )
    text = models.CharField(max_length=500, verbose_name="Texto")

    class Meta(BaseModel.Meta):
        verbose_name = "Highlight"
        verbose_name_plural = "Highlights"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.event_id} / {self.text[:40]}"


class HighlightPhoto(BaseModel):
    highlight = models.ForeignKey(
        Highlight,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Highlight",
    )
    photo = models.ForeignKey(
        "media.Photo",
        on_delete=models.CASCADE,
        related_name="highlight_links",
        verbose_name="Foto",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Foto do highlight"
        verbose_name_plural = "Fotos do highlight"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["highlight", "photo"],
                name="events_highlight_photo_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.highlight_id} / {self.photo_id}"
