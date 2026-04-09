"""k-protect backend configuration.

Reads from environment. KP_TENNETCTL_API_URL is the upstream tennetctl backend.
KP_DATABASE_URL is used for kprotect-specific tables in the 11_kprotect schema.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    tennetctl_api_url: str = Field(
        default="http://localhost:58000",
        alias="KP_TENNETCTL_API_URL",
        description="Upstream tennetctl backend URL to proxy IAM/auth requests to.",
    )
    database_url: str = Field(
        default="postgresql://tennetctl_write:tennetctl_write@localhost:55432/tennetctl",
        alias="KP_DATABASE_URL",
        description="Postgres DSN for the 11_kprotect schema.",
    )
    kbio_api_url: str = Field(
        default="http://localhost:8100",
        alias="KP_KBIO_API_URL",
        description="k-forensics / kbio backend URL for fetching behavioral scores.",
    )
    kbio_service_token: str = Field(
        default="kbio-dev-internal-token",
        alias="KP_KBIO_SERVICE_TOKEN",
        description="Shared secret for kprotect-to-kbio service auth.",
    )
    valkey_url: str = Field(
        default="redis://localhost:6379/0",
        alias="KP_VALKEY_URL",
        description="Valkey (Redis-compatible) URL for kprotect hot cache.",
    )
    env: str = Field(
        default="dev",
        alias="KP_ENV",
        description="Deployment environment.",
    )
    allowed_origins: str = Field(
        default="http://localhost:3200,http://127.0.0.1:3200",
        alias="ALLOWED_ORIGINS",
        description="Comma-separated CORS origins.",
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
