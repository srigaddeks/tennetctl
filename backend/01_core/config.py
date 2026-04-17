"""
TennetCTL configuration — loads from environment variables.

Config is a frozen dataclass. Immutable after creation.

Env-var contract (ADR-028):
  Allowed TENNETCTL_* vars are listed in _ALLOWED_TENNET_ENV. Any other
  TENNETCTL_* variable whose name looks like a secret (matches SECRET|TOKEN|
  PASSWORD|PRIVATE_KEY|API_KEY) blocks startup. Secrets belong in the vault.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

_DEFAULT_MODULES = "core,iam,audit,featureflags,vault,notify"
_DEFAULT_PORT = 51734

_ALLOWED_TENNET_ENV = frozenset({
    "TENNETCTL_VAULT_ROOT_KEY",
    "TENNETCTL_MODULES",
    "TENNETCTL_SINGLE_TENANT",
    "TENNETCTL_APP_PORT",
    "TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT",
})

_SECRETISH_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Config:
    database_url: str
    modules: frozenset[str]
    single_tenant: bool
    app_port: int
    debug: bool
    allow_unauthenticated_vault: bool


def _enforce_env_contract() -> None:
    """Block startup when any TENNETCTL_* env var looks like a secret outside the allowlist."""
    stray_secretish = []
    stray_unknown = []
    for name in os.environ:
        if not name.startswith("TENNETCTL_"):
            continue
        if name in _ALLOWED_TENNET_ENV:
            continue
        if _SECRETISH_RE.search(name):
            stray_secretish.append(name)
        else:
            stray_unknown.append(name)

    if stray_secretish:
        raise RuntimeError(
            "Secrets must live in the vault, not in env.\n"
            f"  Forbidden TENNETCTL_* vars: {sorted(stray_secretish)}\n"
            f"  Allowed TENNETCTL_* vars:   {sorted(_ALLOWED_TENNET_ENV)}\n"
            "See ADR-028 + .env.example.\n"
            "Move these to the vault: POST /v1/vault {'key': '<lowercase.dotted>', 'value': '<value>'}"
        )
    # Unknown non-secretish TENNETCTL_* vars are logged at startup, not blocking.


def load_config() -> Config:
    """Load configuration from environment variables with sensible defaults."""
    _enforce_env_contract()

    modules_str = os.environ.get("TENNETCTL_MODULES", _DEFAULT_MODULES)
    modules = frozenset(m.strip() for m in modules_str.split(",") if m.strip())

    single_tenant = os.environ.get("TENNETCTL_SINGLE_TENANT", "false").lower() in (
        "true", "1", "yes",
    )
    allow_unauth_vault = os.environ.get(
        "TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT", "false",
    ).lower() in ("true", "1", "yes")

    return Config(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
        ),
        modules=modules,
        single_tenant=single_tenant,
        app_port=int(
            os.environ.get("TENNETCTL_APP_PORT", os.environ.get("APP_PORT", str(_DEFAULT_PORT)))
        ),
        debug=os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes"),
        allow_unauthenticated_vault=allow_unauth_vault,
    )
