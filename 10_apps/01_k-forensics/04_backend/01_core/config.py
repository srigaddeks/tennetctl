"""k-forensics backend configuration.

Reads from environment. KF_TENNETCTL_API_URL is the upstream tennetctl backend.
KF_DATABASE_URL will be used for forensics-specific tables (Phase 2).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    tennetctl_api_url: str = Field(
        default="http://localhost:58000",
        alias="KF_TENNETCTL_API_URL",
        description="Upstream tennetctl backend URL to proxy IAM/auth requests to.",
    )
    database_url: str = Field(
        default="",
        alias="KF_DATABASE_URL",
        description="Forensics-specific Postgres DSN (Phase 2).",
    )
    env: str = Field(
        default="dev",
        alias="KF_ENV",
        description="Deployment environment.",
    )
    allowed_origins: str = Field(
        default="http://localhost:3100,http://127.0.0.1:3100",
        alias="ALLOWED_ORIGINS",
        description="Comma-separated CORS origins.",
    )
    kbio_database_url: str = Field(
        default="postgresql://tennetctl_write:tennetctl_write@localhost:55432/tennetctl",
        alias="KF_KBIO_DATABASE_URL",
        description="Postgres DSN for the 10_kbio schema.",
    )
    valkey_url: str = Field(
        default="redis://localhost:6379/0",
        alias="KF_VALKEY_URL",
        description="Valkey (Redis-compatible) URL for kbio hot cache.",
    )
    kbio_internal_service_token: str = Field(
        default="kbio-dev-internal-token",
        alias="KF_KBIO_INTERNAL_SERVICE_TOKEN",
        description="Shared secret for kprotect-to-kbio service auth.",
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        alias="KF_QDRANT_URL",
        description="Qdrant vector DB URL for kbio embeddings.",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
