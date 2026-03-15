"""S3-compatible object storage adapter."""

from __future__ import annotations

from urllib.parse import quote

import boto3
import structlog
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.application.ports.storage import ObjectStorage
from app.config.settings import Settings
from app.domain.entities import StoredObject
from app.domain.exceptions import StorageOperationError

logger = structlog.get_logger(__name__)


class S3ObjectStorage(ObjectStorage):
    """Store recipe images in an S3-compatible bucket."""

    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings
        self._client = self._build_client()

    def _build_client(self) -> BaseClient:
        return boto3.client(
            "s3",
            endpoint_url=self._settings.s3_endpoint_url,
            region_name=self._settings.s3_region_name,
            aws_access_key_id=self._settings.s3_access_key_id,
            aws_secret_access_key=self._settings.s3_secret_access_key.get_secret_value(),
            use_ssl=self._settings.s3_use_ssl,
            config=Config(
                connect_timeout=self._settings.http_connect_timeout_seconds,
                read_timeout=self._settings.request_timeout_seconds,
                retries={"max_attempts": 0},
            ),
        )

    def upload_bytes(
        self,
        *,
        storage_key: str,
        content_bytes: bytes,
        content_type: str,
    ) -> StoredObject:
        """Upload bytes to the configured bucket."""

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._settings.openai_max_retry_attempts),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type((BotoCoreError, ClientError)),
                reraise=True,
            ):
                with attempt:
                    self._client.put_object(
                        Bucket=self._settings.s3_bucket_name,
                        Key=storage_key,
                        Body=content_bytes,
                        ContentType=content_type,
                    )
        except (BotoCoreError, ClientError) as error:
            raise StorageOperationError("Failed to upload image to object storage.") from error

        public_url = None
        if self._settings.s3_public_base_url:
            public_url = (
                f"{self._settings.s3_public_base_url.rstrip('/')}/{quote(storage_key, safe='/')}"
            )

        logger.info("storage.upload.completed", storage_key=storage_key)
        return StoredObject(storage_key=storage_key, public_url=public_url)

    def delete_object(self, *, storage_key: str) -> None:
        """Delete an object from storage."""

        try:
            self._client.delete_object(Bucket=self._settings.s3_bucket_name, Key=storage_key)
        except (BotoCoreError, ClientError) as error:
            raise StorageOperationError("Failed to delete object from storage.") from error

    def build_read_url(self, *, storage_key: str) -> str:
        """Build a public URL or a signed URL for an object."""

        if self._settings.s3_public_base_url:
            return f"{self._settings.s3_public_base_url.rstrip('/')}/{quote(storage_key, safe='/')}"

        try:
            return self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._settings.s3_bucket_name, "Key": storage_key},
                ExpiresIn=self._settings.s3_presigned_url_expiration_seconds,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageOperationError("Failed to generate object read URL.") from error

    def check_bucket_access(self) -> bool:
        """Check whether the configured bucket is reachable."""

        self._client.head_bucket(Bucket=self._settings.s3_bucket_name)
        return True
