from pathlib import Path
from typing import Final
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction

from cabulous.config import get_settings
from media.models import Photo
from media.services.presign import (
    build_s3_client as _build_s3_client,
)
from media.services.presign import (
    presigned_put_url,
    signed_upload_response,
)
from users.models import User

MAX_UPLOAD_BATCH: Final[int] = 50
MAX_PHOTO_SIZE_BYTES: Final[int] = 25 * 1024 * 1024
ALLOWED_CONTENT_TYPES: Final[dict[str, set[str]]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/gif": {".gif"},
}


def generate_photo_upload_signed_url(
    *,
    user_id: str,
    filename: str,
    content_type: str,
) -> dict[str, object]:
    settings = get_settings()
    if not settings.minio.enabled:
        raise ValidationError("Signed upload URL is unavailable because MinIO is disabled.")

    suffix = Path(filename).suffix.lower()
    object_key = f"media/photos/{user_id}/{uuid4().hex}{suffix}"

    s3_client = _build_s3_client(settings.minio.public_endpoint)
    upload_url = presigned_put_url(
        s3_client=s3_client,
        bucket_name=settings.minio.bucket_name,
        object_key=object_key,
        content_type=content_type,
    )
    return signed_upload_response(
        object_key=object_key,
        content_type=content_type,
        upload_url=upload_url,
    )


def confirm_upload(*, user: User, photos_data: list[dict]) -> list[Photo]:
    storage = default_storage
    expected_prefix = f"media/photos/{user.id}/"
    validated: list[Photo] = []

    for data in photos_data:
        object_key = data["object_key"]
        declared_content_type = data["content_type"]
        declared_size = data["size_bytes"]

        if declared_size > MAX_PHOTO_SIZE_BYTES:
            raise ValidationError(f"Declared size {declared_size} exceeds limit for {object_key}.")

        if not object_key.startswith(expected_prefix):
            raise ValidationError(f"Invalid object key prefix for {object_key}.")

        head = storage.head(object_key)  # type: ignore[attr-defined]
        actual_content_type = head["content_type"]
        actual_size = head["content_length"]

        if actual_content_type != declared_content_type:
            raise ValidationError(
                f"MIME type mismatch for {object_key}: "
                f"declared {declared_content_type}, actual {actual_content_type}."
            )

        if actual_size > MAX_PHOTO_SIZE_BYTES:
            raise ValidationError(f"File too large for {object_key}: {actual_size} bytes.")

        validated.append(
            Photo(
                object_key=object_key,
                uploader=user,
                taken_on=data["taken_on"],
                caption=data.get("caption", ""),
                content_type=declared_content_type,
                size_bytes=actual_size,
            )
        )

    with transaction.atomic():
        return Photo.objects.bulk_create(validated)
