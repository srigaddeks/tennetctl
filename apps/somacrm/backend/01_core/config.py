"""
somacrm configuration — frozen dataclass loaded from environment variables.

NO BaseSettings (project precedent). NO secrets in *_API_KEY env vars beyond
the bootstrap service key — runtime secrets live in the tennetctl vault.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    # Postgres (somacrm uses tennetctl's Postgres, separate schema "12_somacrm")
    pg_host: str
    pg_port: int
    pg_user: str
    pg_pass: str
    pg_db: str

    # somacrm app
    somacrm_port: int
    somacrm_debug: bool
    somacrm_frontend_origin: str

    # tennetctl proxy
    tennetctl_base_url: str
    tennetctl_service_api_key: str | None

    # cross-app links
    somaerp_base_url: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_pass}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )


def load_config() -> Config:
    pg_pass = os.environ.get("SOMACRM_PG_PASS", "tennetctl_dev")

    return Config(
        pg_host=os.environ.get("SOMACRM_PG_HOST", "localhost"),
        pg_port=int(os.environ.get("SOMACRM_PG_PORT", "5434")),
        pg_user=os.environ.get("SOMACRM_PG_USER", "tennetctl"),
        pg_pass=pg_pass,
        pg_db=os.environ.get("SOMACRM_PG_DB", "tennetctl"),
        somacrm_port=int(os.environ.get("SOMACRM_PORT", "51738")),
        somacrm_debug=_bool(os.environ.get("SOMACRM_DEBUG"), default=False),
        somacrm_frontend_origin=os.environ.get(
            "SOMACRM_FRONTEND_ORIGIN", "http://localhost:51739",
        ),
        tennetctl_base_url=os.environ.get(
            "TENNETCTL_BASE_URL", "http://localhost:51734",
        ),
        tennetctl_service_api_key=os.environ.get("TENNETCTL_SERVICE_API_KEY"),
        somaerp_base_url=os.environ.get("SOMAERP_BASE_URL", "http://localhost:51736"),
    )
