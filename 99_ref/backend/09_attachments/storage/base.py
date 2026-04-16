"""Abstract base for object storage providers.

Providers must implement: upload, generate_presigned_download_url, delete,
get_file_size, and health_check.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class UploadResult:
    storage_key: str
    storage_bucket: str
    storage_provider: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str


@dataclass(frozen=True)
class PresignedUrlResult:
    url: str
    expires_at: datetime
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a storage provider connectivity check."""
    provider: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None


class StorageProvider(ABC):
    """Abstract base class for all storage provider implementations."""

    @abstractmethod
    async def upload(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> UploadResult:
        """Upload file bytes to object storage. Returns upload result with metadata."""
        ...

    @abstractmethod
    async def generate_presigned_download_url(
        self,
        storage_key: str,
        filename: str,
        expires_seconds: int = 3600,
    ) -> PresignedUrlResult:
        """Generate a presigned URL for downloading a file. URL expires after expires_seconds."""
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """Permanently delete a file from object storage."""
        ...

    @abstractmethod
    async def get_file_size(self, storage_key: str) -> int:
        """Return the stored file size in bytes."""
        ...

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """Verify connectivity to the storage backend.

        Should attempt a lightweight operation (e.g., head bucket / list one object)
        and return timing information.  Must not raise — return HealthCheckResult
        with healthy=False and error message on failure.
        """
        ...
