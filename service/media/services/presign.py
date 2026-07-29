from typing import Final

import boto3
from django.core.files.storage import default_storage
from mypy_boto3_s3.client import S3Client

from cabulous.config import get_settings

SIGNED_URL_EXPIRES_IN_SECONDS: Final[int] = 300


def build_s3_client(endpoint_url: str) -> S3Client:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio.access_key,
        aws_secret_access_key=settings.minio.secret_key,
        region_name=settings.minio.region_name,
    )


def build_storage_object_key(object_key: str) -> str:
    storage_location = str(getattr(default_storage, "location", "") or "").strip("/")
    normalized_key = object_key.strip("/")
    if storage_location:
        return f"{storage_location}/{normalized_key}"
    return normalized_key


def presigned_put_url(
    *,
    s3_client: S3Client,
    bucket_name: str,
    object_key: str,
    content_type: str,
) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket_name,
            "Key": build_storage_object_key(object_key),
            "ContentType": content_type,
        },
        ExpiresIn=SIGNED_URL_EXPIRES_IN_SECONDS,
    )


def signed_upload_response(
    *,
    object_key: str,
    content_type: str,
    upload_url: str,
) -> dict[str, object]:
    return {
        "upload_url": upload_url,
        "method": "PUT",
        "headers": {"Content-Type": content_type},
        "object_key": object_key,
        "expires_in": SIGNED_URL_EXPIRES_IN_SECONDS,
    }
