from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from importlib import import_module

from .base import HealthCheckResult, StorageProvider, UploadResult, PresignedUrlResult

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger

_LOGGER = get_logger("backend.attachments.storage.azure")


class AzureProvider(StorageProvider):
    """Azure Blob Storage provider using azure-storage-blob."""

    def __init__(self, settings) -> None:
        self._container = settings.storage_azure_container
        self._account_name = settings.storage_azure_account_name or None
        self._account_key = settings.storage_azure_account_key or None
        self._connection_string = settings.storage_azure_connection_string or None

    def _get_client(self):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise RuntimeError(
                "azure-storage-blob is required for Azure storage. "
                "Install it with: pip install azure-storage-blob"
            ) from exc

        if self._connection_string:
            return BlobServiceClient.from_connection_string(self._connection_string)
        if self._account_name and self._account_key:
            account_url = f"https://{self._account_name}.blob.core.windows.net"
            from azure.storage.blob import StorageSharedKeyCredential
            credential = StorageSharedKeyCredential(self._account_name, self._account_key)
            return BlobServiceClient(account_url=account_url, credential=credential)
        raise ValueError(
            "Azure storage requires either STORAGE_AZURE_CONNECTION_STRING or "
            "STORAGE_AZURE_ACCOUNT_NAME + STORAGE_AZURE_ACCOUNT_KEY."
        )

    async def upload(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> UploadResult:
        try:
            from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
        except ImportError as exc:
            raise RuntimeError(
                "azure-storage-blob is required for Azure storage. "
                "Install it with: pip install azure-storage-blob"
            ) from exc

        checksum = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)

        if self._connection_string:
            client = AsyncBlobServiceClient.from_connection_string(self._connection_string)
        elif self._account_name and self._account_key:
            from azure.storage.blob import StorageSharedKeyCredential
            account_url = f"https://{self._account_name}.blob.core.windows.net"
            credential = StorageSharedKeyCredential(self._account_name, self._account_key)
            client = AsyncBlobServiceClient(account_url=account_url, credential=credential)
        else:
            raise ValueError("Azure storage credentials not configured.")

        async with client:
            blob_client = client.get_blob_client(container=self._container, blob=storage_key)
            await blob_client.upload_blob(
                file_data,
                overwrite=True,
                content_settings=self._content_settings(content_type),
                metadata={k: str(v) for k, v in metadata.items()},
            )

        _LOGGER.info(
            "azure_upload_complete",
            extra={
                "action": "storage.upload",
                "outcome": "success",
                "storage_key": storage_key,
                "file_size_bytes": file_size,
                "provider": "azure",
            },
        )

        return UploadResult(
            storage_key=storage_key,
            storage_bucket=self._container,
            storage_provider="azure",
            content_type=content_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
        )

    def _content_settings(self, content_type: str):
        from azure.storage.blob import ContentSettings
        return ContentSettings(content_type=content_type)

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

        def _generate_sas():
            from azure.storage.blob import (
                generate_blob_sas,
                BlobSasPermissions,
            )
            if not self._account_name or not self._account_key:
                raise ValueError(
                    "Azure SAS URL generation requires STORAGE_AZURE_ACCOUNT_NAME and "
                    "STORAGE_AZURE_ACCOUNT_KEY."
                )
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)
            sas_token = generate_blob_sas(
                account_name=self._account_name,
                container_name=self._container,
                blob_name=storage_key,
                account_key=self._account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry,
                content_disposition=content_disposition,
            )
            url = (
                f"https://{self._account_name}.blob.core.windows.net"
                f"/{self._container}/{storage_key}?{sas_token}"
            )
            return url, expiry

        loop = asyncio.get_event_loop()
        url, expires_at = await loop.run_in_executor(None, _generate_sas)

        return PresignedUrlResult(
            url=url,
            expires_at=expires_at,
            headers={"Content-Disposition": content_disposition},
        )

    async def delete(self, storage_key: str) -> None:
        try:
            from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
        except ImportError as exc:
            raise RuntimeError(
                "azure-storage-blob is required for Azure storage. "
                "Install it with: pip install azure-storage-blob"
            ) from exc

        if self._connection_string:
            client = AsyncBlobServiceClient.from_connection_string(self._connection_string)
        elif self._account_name and self._account_key:
            from azure.storage.blob import StorageSharedKeyCredential
            account_url = f"https://{self._account_name}.blob.core.windows.net"
            credential = StorageSharedKeyCredential(self._account_name, self._account_key)
            client = AsyncBlobServiceClient(account_url=account_url, credential=credential)
        else:
            raise ValueError("Azure storage credentials not configured.")

        async with client:
            blob_client = client.get_blob_client(container=self._container, blob=storage_key)
            await blob_client.delete_blob()

        _LOGGER.info(
            "azure_delete_complete",
            extra={
                "action": "storage.delete",
                "outcome": "success",
                "storage_key": storage_key,
                "provider": "azure",
            },
        )

    async def get_file_size(self, storage_key: str) -> int:
        import asyncio

        def _do_stat():
            service_client = self._get_client()
            blob_client = service_client.get_blob_client(
                container=self._container, blob=storage_key
            )
            props = blob_client.get_blob_properties()
            return props.size

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _do_stat)

    async def health_check(self) -> HealthCheckResult:
        """Check Azure Blob Storage container accessibility via a lightweight exists() call."""
        import asyncio
        import time

        t0 = time.monotonic()
        try:
            def _do_check():
                service_client = self._get_client()
                container_client = service_client.get_container_client(self._container)
                container_client.get_container_properties()  # Lightweight metadata fetch

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _do_check)
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider="azure",
                healthy=True,
                latency_ms=latency_ms,
            )
        except Exception:
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return HealthCheckResult(
                provider="azure",
                healthy=False,
                latency_ms=latency_ms,
                error="Storage unavailable.",
            )
