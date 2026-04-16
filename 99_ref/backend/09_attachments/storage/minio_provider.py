from __future__ import annotations

from importlib import import_module

from .s3_provider import S3Provider

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger

_LOGGER = get_logger("backend.attachments.storage.minio")


class MinIOProvider(S3Provider):
    """MinIO storage provider — reuses S3Provider with MinIO endpoint URL.

    MinIO is S3-compatible, so all S3 API calls work identically.
    The only difference is using STORAGE_MINIO_ENDPOINT_URL for the endpoint.
    """

    def __init__(self, settings) -> None:
        # Delegate to S3Provider but override endpoint to MinIO
        # We temporarily swap the endpoint_url in settings-derived attrs
        super().__init__(settings)
        # Override: MinIO has its own endpoint setting
        self._endpoint_url = settings.storage_minio_endpoint_url or settings.storage_s3_endpoint_url or None
        self._bucket = settings.storage_minio_bucket or settings.storage_s3_bucket
        self._provider_name = "minio"

    def _client_kwargs(self) -> dict:
        kwargs: dict = {}
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return kwargs
