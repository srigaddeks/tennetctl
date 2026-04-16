from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from importlib import import_module

from .base import HealthCheckResult, StorageProvider, UploadResult, PresignedUrlResult

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger

_LOGGER = get_logger("backend.attachments.storage.gcs")


class GCSProvider(StorageProvider):
    """Google Cloud Storage provider using google-cloud-storage."""

    def __init__(self, settings) -> None:
        self._bucket_name = settings.storage_gcs_bucket
        self._project = settings.storage_gcs_project or None
        self._credentials_json = settings.storage_gcs_credentials_json or None

    def _get_client(self):
        try:
            from google.cloud import storage as gcs_storage
            from google.oauth2 import service_account
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-storage is required for GCS storage. "
                "Install it with: pip install google-cloud-storage"
            ) from exc

        if self._credentials_json:
            credentials_info = json.loads(self._credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            client = gcs_storage.Client(project=self._project, credentials=credentials)
        else:
            # Use application default credentials
            client = gcs_storage.Client(project=self._project)
        return client

    async def upload(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> UploadResult:
        import asyncio
        checksum = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)

        def _do_upload():
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(storage_key)
            blob.metadata = {k: str(v) for k, v in metadata.items()}
            blob.upload_from_string(file_data, content_type=content_type)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _do_upload)

        _LOGGER.info(
            "gcs_upload_complete",
            extra={
                "action": "storage.upload",
                "outcome": "success",
                "storage_key": storage_key,
                "file_size_bytes": file_size,
                "provider": "gcs",
            },
        )

        return UploadResult(
            storage_key=storage_key,
            storage_bucket=self._bucket_name,
            storage_provider="gcs",
            content_type=content_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
        )

    async def generate_presigned_download_url(
        self,
        storage_key: str,
        filename: str,
        expires_seconds: int = 3600,
    ) -> PresignedUrlResult:
        import asyncio
        import urllib.parse
        safe_filename = urllib.parse.quote(filename)
        content_disposition = f'attachment; filename="{safe_filename}"'

        def _do_sign():
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(storage_key)
            expiration = timedelta(seconds=expires_seconds)
            url = blob.generate_signed_url(
                expiration=expiration,
                method="GET",
                response_disposition=content_disposition,
                version="v4",
            )
            return url

        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(None, _do_sign)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)

        return PresignedUrlResult(
            url=url,
            expires_at=expires_at,
            headers={"Content-Disposition": content_disposition},
        )

    async def delete(self, storage_key: str) -> None:
        import asyncio

        def _do_delete():
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(storage_key)
            blob.delete()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _do_delete)

        _LOGGER.info(
            "gcs_delete_complete",
            extra={
                "action": "storage.delete",
                "outcome": "success",
                "storage_key": storage_key,
                "provider": "gcs",
            },
        )

    async def get_file_size(self, storage_key: str) -> int:
        import asyncio

        def _do_stat():
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.get_blob(storage_key)
            if blob is None:
                raise FileNotFoundError(f"Object not found: {storage_key}")
            return blob.size

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _do_stat)

    async def health_check(self) -> HealthCheckResult:
        """Check GCS bucket accessibility via a lightweight bucket.exists() call."""
        import asyncio
        import time

        t0 = time.monotonic()
        try:
            def _do_check():
                client = self._get_client()
                bucket = client.bucket(self._bucket_name)
                bucket.reload()  # Fetches bucket metadata — lightweight IAM check

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _do_check)
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider="gcs",
                healthy=True,
                latency_ms=latency_ms,
            )
        except Exception:
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider="gcs",
                healthy=False,
                latency_ms=latency_ms,
                error="Storage unavailable.",
            )
