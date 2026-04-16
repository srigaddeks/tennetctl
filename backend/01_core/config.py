"""
TennetCTL configuration — loads from environment variables.

Config is a frozen dataclass. Immutable after creation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

_DEFAULT_MODULES = "core,iam,audit"
_DEFAULT_PORT = 51734


@dataclass(frozen=True)
class Config:
    database_url: str
    modules: frozenset[str]
    single_tenant: bool
    app_port: int
    debug: bool


def load_config() -> Config:
    """Load configuration from environment variables with sensible defaults."""
    modules_str = os.environ.get("TENNETCTL_MODULES", _DEFAULT_MODULES)
    modules = frozenset(m.strip() for m in modules_str.split(",") if m.strip())

    single_tenant = os.environ.get("TENNETCTL_SINGLE_TENANT", "false").lower() in (
        "true", "1", "yes",
    )

    return Config(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
        ),
        modules=modules,
        single_tenant=single_tenant,
        app_port=int(os.environ.get("APP_PORT", str(_DEFAULT_PORT))),
        debug=os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes"),
    )
