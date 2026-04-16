from __future__ import annotations

from .base import StorageProvider


def get_storage_provider(settings) -> StorageProvider:
    """Return the appropriate StorageProvider based on STORAGE_PROVIDER setting.

    Supported providers:
        s3    — AWS S3 (requires aioboto3)
        gcs   — Google Cloud Storage (requires google-cloud-storage)
        azure — Azure Blob Storage (requires azure-storage-blob)
        minio — MinIO S3-compatible (requires aioboto3, uses STORAGE_MINIO_ENDPOINT_URL)
    """
    provider_type: str = (settings.storage_provider or "minio").lower().strip()

    match provider_type:
        case "s3":
            from .s3_provider import S3Provider
            return S3Provider(settings)
        case "gcs":
            from .gcs_provider import GCSProvider
            return GCSProvider(settings)
        case "azure":
            from .azure_provider import AzureProvider
            return AzureProvider(settings)
        case "minio":
            from .minio_provider import MinIOProvider
            return MinIOProvider(settings)
        case _:
            raise ValueError(
                f"Unknown storage provider: {provider_type!r}. "
                "Valid options: s3, gcs, azure, minio"
            )
