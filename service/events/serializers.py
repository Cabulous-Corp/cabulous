from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from events.constants import EVENT_TYPE_COLOR_MAP
from events.enums import Audience, EventType
from events.models import Event, EventLocation, EventParticipant, EventPhoto, Highlight


class EventLocationWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False, default="")
    address = serializers.CharField()
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )


class EventLocationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLocation
        fields = ["id", "name", "address", "latitude", "longitude"]
        read_only_fields = fields


class EventCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    type = serializers.ChoiceField(choices=EventType.choices)
    audiences = serializers.ListField(
        child=serializers.ChoiceField(choices=Audience.choices),
        min_length=1,
    )
    location = EventLocationWriteSerializer(required=False, default=None)

    def validate(self, data):
        if data["end_at"] < data["start_at"]:
            raise serializers.ValidationError({"end_at": "End date must not be before start date."})
        return data


class EventReadSerializer(serializers.ModelSerializer):
    audiences = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    type_color = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    location = EventLocationReadSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "start_at",
            "end_at",
            "type",
            "type_color",
            "status",
            "cancelled_at",
            "audiences",
            "participants_count",
            "location",
            "thumbnail_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_audiences(self, obj) -> list[str]:
        return [a.audience for a in obj.audiences.all()]

    def get_participants_count(self, obj) -> int:
        return len(obj.participants.all())

    def get_type_color(self, obj) -> str:
        try:
            return EVENT_TYPE_COLOR_MAP.get(EventType(obj.type), "#FFFFFF")
        except ValueError:
            return "#FFFFFF"

    def get_thumbnail_url(self, obj) -> str | None:
        for p in obj.photos.all():
            if p.is_thumbnail:
                return p.photo.object_key
        return None


class EventUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)
    type = serializers.ChoiceField(choices=EventType.choices, required=False)
    audiences = serializers.ListField(
        child=serializers.ChoiceField(choices=Audience.choices),
        min_length=1,
        required=False,
    )
    location = EventLocationWriteSerializer(required=False)

    def validate(self, data):
        start = data.get("start_at") or getattr(self.instance, "start_at", None)
        end = data.get("end_at") or getattr(self.instance, "end_at", None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_at": "End date must not be before start date."})
        return data


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------


class ParticipantAddSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


class ParticipantReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = EventParticipant
        fields = ["id", "user", "username", "created_at"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Event Photos
# ---------------------------------------------------------------------------


class PhotoLinkSerializer(serializers.Serializer):
    photo_id = serializers.UUIDField()


class EventPhotoReadSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(source="photo.content_type", read_only=True)
    object_key = serializers.CharField(source="photo.object_key", read_only=True)

    class Meta:
        model = EventPhoto
        fields = ["id", "photo", "content_type", "object_key", "is_thumbnail", "created_at"]
        read_only_fields = fields


class ThumbnailSerializer(serializers.Serializer):
    photo_id = serializers.UUIDField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# Highlights
# ---------------------------------------------------------------------------


class HighlightPhotoReadSerializer(serializers.Serializer):
    """Lightweight read serializer for a photo linked to a highlight."""

    id = serializers.UUIDField(source="photo.id", read_only=True)
    object_key = serializers.CharField(source="photo.object_key", read_only=True)
    content_type = serializers.CharField(source="photo.content_type", read_only=True)


class HighlightReadSerializer(serializers.ModelSerializer):
    photos = HighlightPhotoReadSerializer(many=True, read_only=True)
    author_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Highlight
        fields = ["id", "text", "author_id", "photos", "created_at", "updated_at"]
        read_only_fields = fields


class HighlightWriteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(max_length=500)
    photo_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)

    class Meta:
        model = Highlight
        fields = ["text", "photo_ids"]
