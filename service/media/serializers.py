from pathlib import Path

from rest_framework import serializers

from media.models import Photo
from media.services.upload_signing import ALLOWED_CONTENT_TYPES


class FileUploadItemSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)


class PhotoUploadUrlsRequestSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=FileUploadItemSerializer(),
        min_length=1,
        max_length=50,
    )

    def validate_files(self, value: list[dict]) -> list[dict]:
        for item in value:
            content_type = item["content_type"]
            filename = item["filename"]
            suffix = Path(filename).suffix.lower()

            if content_type not in ALLOWED_CONTENT_TYPES:
                raise serializers.ValidationError(f"Unsupported content type: {content_type}.")

            if suffix not in ALLOWED_CONTENT_TYPES[content_type]:
                raise serializers.ValidationError(
                    f"Extension {suffix} does not match content type {content_type}."
                )

        return value


class PhotoConfirmItemSerializer(serializers.Serializer):
    object_key = serializers.CharField(max_length=1024)
    taken_on = serializers.DateField()
    caption = serializers.CharField(required=False, allow_blank=True, default="")
    content_type = serializers.CharField(max_length=100)
    size_bytes = serializers.IntegerField(min_value=0)


class PhotoConfirmRequestSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=PhotoConfirmItemSerializer(),
        min_length=1,
        max_length=50,
    )


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = [
            "id",
            "object_key",
            "uploader",
            "taken_on",
            "caption",
            "content_type",
            "size_bytes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "object_key",
            "uploader",
            "content_type",
            "size_bytes",
            "created_at",
            "updated_at",
        ]
