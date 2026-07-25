from pathlib import Path
from typing import Final
from uuid import uuid4

import boto3
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from mypy_boto3_s3.client import S3Client

from cabulous.config import get_settings
from media.models import Photo
from users.models import User

SIGNED_URL_EXPIRES_IN_SECONDS: Final[int] = 300
MAX_UPLOAD_BATCH: Final[int] = 50
MAX_PHOTO_SIZE_BYTES: Final[int] = 25 * 1024 * 1024
ALLOWED_CONTENT_TYPES: Final[dict[str, set[str]]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/gif": {".gif"},
}


def _build_s3_client(endpoint_url: str) -> S3Client:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio.access_key,
        aws_secret_access_key=settings.minio.secret_key,
        region_name=settings.minio.region_name,
    )


def _build_storage_object_key(object_key: str) -> str:
    storage_location = str(getattr(default_storage, "location", "") or "").strip("/")
    normalized_key = object_key.strip("/")
    if storage_location:
        return f"{storage_location}/{normalized_key}"
    return normalized_key


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
    storage_object_key = _build_storage_object_key(object_key)
    upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.minio.bucket_name,
            "Key": storage_object_key,
            "ContentType": content_type,
        },
        ExpiresIn=SIGNED_URL_EXPIRES_IN_SECONDS,
    )
    return {
        "upload_url": upload_url,
        "method": "PUT",
        "headers": {"Content-Type": content_type},
        "object_key": object_key,
        "expires_in": SIGNED_URL_EXPIRES_IN_SECONDS,
    }


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
