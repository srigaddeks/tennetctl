"""AWS S3 / S3-compatible storage provider using aioboto3.

Supports both AWS S3 and any S3-compatible endpoint (MinIO, Ceph, etc.) via
the ``endpoint_url`` setting.  Large files (>= 10 MB) are uploaded using
S3 multipart upload for reliability.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone, timedelta
from importlib import import_module
from typing import TYPE_CHECKING

from .base import HealthCheckResult, StorageProvider, UploadResult, PresignedUrlResult

if TYPE_CHECKING:
    pass

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger

_LOGGER = get_logger("backend.attachments.storage.s3")

# Chunked upload threshold: files >= 10 MB use multipart upload
_MULTIPART_THRESHOLD_BYTES = 10 * 1024 * 1024
_MULTIPART_CHUNK_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB minimum part size for S3


class S3Provider(StorageProvider):
    """AWS S3 storage provider using aioboto3 (async boto3)."""

    def __init__(self, settings) -> None:
        self._bucket = settings.storage_s3_bucket
        self._region = settings.storage_s3_region
        self._access_key_id = settings.storage_s3_access_key_id or None
        self._secret_access_key = settings.storage_s3_secret_access_key or None
        self._endpoint_url = settings.storage_s3_endpoint_url or None
        self._provider_name = "s3"

    def _get_session(self):
        try:
            import aioboto3
        except ImportError as exc:
            raise RuntimeError(
                "aioboto3 is required for S3 storage. Install it with: pip install aioboto3"
            ) from exc
        session = aioboto3.Session(
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name=self._region,
        )
        return session

    def _client_kwargs(self) -> dict:
        kwargs: dict = {}
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return kwargs

    async def upload(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> UploadResult:
        checksum = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)

        session = self._get_session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            if file_size >= _MULTIPART_THRESHOLD_BYTES:
                await self._multipart_upload(s3, file_data, storage_key, content_type, metadata)
            else:
                await s3.put_object(
                    Bucket=self._bucket,
                    Key=storage_key,
                    Body=file_data,
                    ContentType=content_type,
                    Metadata={k: str(v) for k, v in metadata.items()},
                )

        _LOGGER.info(
            "s3_upload_complete",
            extra={
                "action": "storage.upload",
                "outcome": "success",
                "storage_key": storage_key,
                "file_size_bytes": file_size,
                "provider": self._provider_name,
            },
        )

        return UploadResult(
            storage_key=storage_key,
            storage_bucket=self._bucket,
            storage_provider=self._provider_name,
            content_type=content_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
        )

    async def _multipart_upload(self, s3, file_data: bytes, storage_key: str, content_type: str, metadata: dict) -> None:
        """Perform S3 multipart upload for large files."""
        response = await s3.create_multipart_upload(
            Bucket=self._bucket,
            Key=storage_key,
            ContentType=content_type,
            Metadata={k: str(v) for k, v in metadata.items()},
        )
        upload_id = response["UploadId"]
        parts = []

        try:
            chunk_number = 1
            offset = 0
            while offset < len(file_data):
                chunk = file_data[offset : offset + _MULTIPART_CHUNK_SIZE_BYTES]
                part_response = await s3.upload_part(
                    Bucket=self._bucket,
                    Key=storage_key,
                    PartNumber=chunk_number,
                    UploadId=upload_id,
                    Body=chunk,
                )
                parts.append({"PartNumber": chunk_number, "ETag": part_response["ETag"]})
                offset += _MULTIPART_CHUNK_SIZE_BYTES
                chunk_number += 1

            await s3.complete_multipart_upload(
                Bucket=self._bucket,
                Key=storage_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
        except Exception:
            await s3.abort_multipart_upload(
                Bucket=self._bucket,
                Key=storage_key,
                UploadId=upload_id,
            )
            raise

    async def generate_presigned_download_url(
        self,
        storage_key: str,
        filename: str,
        expires_seconds: int = 3600,
    ) -> PresignedUrlResult:
        import urllib.parse
        safe_filename = urllib.parse.quote(filename)
        content_disposition = f'attachment; filename="{safe_filename}"'

        session = self._get_session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": storage_key,
                    "ResponseContentDisposition": content_disposition,
                },
                ExpiresIn=expires_seconds,
            )

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)
        return PresignedUrlResult(
            url=url,
            expires_at=expires_at,
            headers={"Content-Disposition": content_disposition},
        )

    async def delete(self, storage_key: str) -> None:
        session = self._get_session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            await s3.delete_object(Bucket=self._bucket, Key=storage_key)
        _LOGGER.info(
            "s3_delete_complete",
            extra={
                "action": "storage.delete",
                "outcome": "success",
                "storage_key": storage_key,
                "provider": self._provider_name,
            },
        )

    async def get_file_size(self, storage_key: str) -> int:
        session = self._get_session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            response = await s3.head_object(Bucket=self._bucket, Key=storage_key)
        return response["ContentLength"]

    async def health_check(self) -> HealthCheckResult:
        """Check S3 bucket accessibility via HeadBucket (lightweight metadata call)."""
        t0 = time.monotonic()
        try:
            session = self._get_session()
            async with session.client("s3", **self._client_kwargs()) as s3:
                await s3.head_bucket(Bucket=self._bucket)
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider=self._provider_name,
                healthy=True,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider=self._provider_name,
                healthy=False,
                latency_ms=latency_ms,
                error="Storage unavailable.",
            )
