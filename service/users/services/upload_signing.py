from pathlib import Path
from typing import Final

from django.core.exceptions import ValidationError

from cabulous.config import get_settings
from media.services.presign import (
    build_s3_client as _build_s3_client,
)
from media.services.presign import (
    presigned_put_url,
    signed_upload_response,
)
from users.models import User, user_avatar_upload_to, user_banner_upload_to

AVATAR_ALLOWED_EXTENSIONS: Final[set[str]] = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_FILE_TYPES: Final[set[str]] = {"avatar", "banner"}


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
        _validate_image_file(filename, content_type)
        return user_avatar_upload_to(user, filename)
    if normalized_file_type == "banner":
        _validate_image_file(filename, content_type)
        return user_banner_upload_to(user, filename)

    raise ValidationError("Unsupported upload file type.")


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
