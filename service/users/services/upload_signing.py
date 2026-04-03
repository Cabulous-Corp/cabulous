import uuid
from pathlib import Path
from typing import Final

import boto3  # type: ignore[import-untyped]
from botocore.client import BaseClient  # type: ignore[import-untyped]
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage

from cabulous.config import get_settings
from users.models import User

SIGNED_URL_EXPIRES_IN_SECONDS: Final[int] = 300
AVATAR_ALLOWED_EXTENSIONS: Final[set[str]] = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_FILE_TYPES: Final[set[str]] = {"avatar", "banner"}


def _build_s3_client(endpoint_url: str) -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio.access_key,
        aws_secret_access_key=settings.minio.secret_key,
        region_name=settings.minio.region_name,
    )


def _validate_upload_type(file_type: str) -> str:
    if file_type not in UPLOAD_FILE_TYPES:
        raise ValidationError("Unsupported upload file type.")
    return file_type


def _validate_image_file(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in AVATAR_ALLOWED_EXTENSIONS:
        raise ValidationError("Unsupported image file extension.")
    if not content_type.startswith("image/"):
        raise ValidationError("Image upload requires an image content type.")
    return suffix


def build_user_upload_key(user: User, file_type: str, filename: str, content_type: str) -> str:
    normalized_file_type = _validate_upload_type(file_type)
    if normalized_file_type == "avatar":
        suffix = _validate_image_file(filename, content_type)
        return f"users/{user.id}/avatar/{uuid.uuid4().hex}{suffix}"
    if normalized_file_type == "banner":
        suffix = _validate_image_file(filename, content_type)
        return f"users/{user.id}/banner/{uuid.uuid4().hex}{suffix}"

    raise ValidationError("Unsupported upload file type.")


def _build_storage_object_key(object_key: str) -> str:
    storage_location = str(getattr(default_storage, "location", "") or "").strip("/")
    normalized_key = object_key.strip("/")
    if storage_location:
        return f"{storage_location}/{normalized_key}"
    return normalized_key


def generate_upload_signed_url(
    *,
    user: User,
    file_type: str,
    filename: str,
    content_type: str,
) -> dict[str, object]:
    settings = get_settings()
    if not settings.minio.enabled:
        raise ValidationError("Signed upload URL is unavailable because MinIO is disabled.")

    object_key = build_user_upload_key(
        user=user,
        file_type=file_type,
        filename=filename,
        content_type=content_type,
    )
    # Signed URLs must use the public endpoint so the frontend/browser can reach MinIO.
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
