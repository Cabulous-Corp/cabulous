from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.client import BaseClient  # type: ignore[import-untyped]
from django.utils.functional import cached_property
from storages.backends.s3 import S3Storage  # type: ignore[import-untyped]
from storages.utils import clean_name  # type: ignore[import-untyped]

from cabulous.config import get_settings


class PublicEndpointMediaStorage(S3Storage):
    """
    Uses internal MinIO endpoint for backend operations, but generates presigned GET URLs
    with the public endpoint so frontend clients can access media files.
    """

    @cached_property
    def public_s3_client(self) -> BaseClient:
        settings = get_settings()
        return boto3.client(
            "s3",
            endpoint_url=settings.minio.public_endpoint,
            aws_access_key_id=settings.minio.access_key,
            aws_secret_access_key=settings.minio.secret_key,
            region_name=settings.minio.region_name,
        )

    def url(
        self,
        name: str,
        parameters: dict[str, Any] | None = None,
        expire: int | None = None,
        http_method: str | None = None,
    ) -> str:
        if not self.querystring_auth:
            return super().url(
                name=name,
                parameters=parameters,
                expire=expire,
                http_method=http_method,
            )

        normalized_name = self._normalize_name(clean_name(name))
        params = {"Bucket": self.bucket_name, "Key": normalized_name}
        if parameters:
            params.update(parameters)

        return self.public_s3_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expire or self.querystring_expire,
            HttpMethod=http_method,
        )
