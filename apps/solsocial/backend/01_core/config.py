"""
SolSocial configuration — loads from environment variables.

Mirrors tennetctl's env-var contract (ADR-028): no secrets in SOLSOCIAL_* vars.
OAuth client secrets and provider tokens belong in the tennetctl vault.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

_DEFAULT_PORT = 51834

_ALLOWED_SOLSOCIAL_ENV = frozenset({
    "SOLSOCIAL_APP_PORT",
    "SOLSOCIAL_TENNETCTL_URL",
    "SOLSOCIAL_TENNETCTL_KEY_FILE",  # path to file containing service API key (nk_...)
    "SOLSOCIAL_APPLICATION_CODE",    # tennetctl application code (default "solsocial")
    "SOLSOCIAL_TENNETCTL_ORG_ID",    # tennetctl org that owns the solsocial application
    "SOLSOCIAL_FRONTEND_ORIGIN",
    "SOLSOCIAL_PUBLISHER_MODE",  # "live" or "stub"
    # Provider OAuth credentials — file paths only, never the secret itself.
    "SOLSOCIAL_LINKEDIN_CLIENT_ID_FILE",
    "SOLSOCIAL_LINKEDIN_CLIENT_SECRET_FILE",
    "SOLSOCIAL_TWITTER_CLIENT_ID_FILE",
    "SOLSOCIAL_TWITTER_CLIENT_SECRET_FILE",
    "SOLSOCIAL_INSTAGRAM_CLIENT_ID_FILE",
    "SOLSOCIAL_INSTAGRAM_CLIENT_SECRET_FILE",
    # Symmetric key for encrypting per-workspace OAuth client_secrets at rest.
    # Auto-generated on first boot if missing.
    "SOLSOCIAL_ENCRYPTION_KEY_FILE",
})

_SECRETISH_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProviderCreds:
    client_id: str | None = None
    client_secret: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


@dataclass(frozen=True)
class Config:
    database_url: str
    app_port: int
    debug: bool
    tennetctl_url: str
    tennetctl_service_api_key: str | None
    application_code: str
    tennetctl_org_id: str | None
    frontend_origin: str
    publisher_mode: str
    linkedin: ProviderCreds
    twitter: ProviderCreds
    instagram: ProviderCreds


def _enforce_env_contract() -> None:
    stray_secretish = []
    for name in os.environ:
        if not name.startswith("SOLSOCIAL_"):
            continue
        if name in _ALLOWED_SOLSOCIAL_ENV:
            continue
        if _SECRETISH_RE.search(name):
            stray_secretish.append(name)
    if stray_secretish:
        raise RuntimeError(
            "Secrets must live in the tennetctl vault, not env.\n"
            f"  Forbidden SOLSOCIAL_* vars: {sorted(stray_secretish)}\n"
            f"  Allowed SOLSOCIAL_* vars: {sorted(_ALLOWED_SOLSOCIAL_ENV)}\n"
            "Store provider OAuth secrets as vault keys: solsocial.oauth.<provider>.client_secret"
        )


def _read_secret_file(env_var: str) -> str | None:
    """Read a secret from a file whose path is given by env var. None if missing."""
    path = os.environ.get(env_var)
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.is_file():
        return None
    v = p.read_text(encoding="utf-8").strip()
    return v or None


def _load_provider(prov: str) -> "ProviderCreds":
    return ProviderCreds(
        client_id=_read_secret_file(f"SOLSOCIAL_{prov.upper()}_CLIENT_ID_FILE"),
        client_secret=_read_secret_file(f"SOLSOCIAL_{prov.upper()}_CLIENT_SECRET_FILE"),
    )


def _load_service_api_key() -> str | None:
    """Read the tennetctl service API key from the file at SOLSOCIAL_TENNETCTL_KEY_FILE.

    The key itself must not sit in an env var (ADR-028 blocks *API_KEY* vars). The
    file path is fine — only the path is persisted in env. Expected file content:
    a single line `nk_<key_id>.<secret>` as returned by POST /v1/api-keys.
    """
    path = os.environ.get("SOLSOCIAL_TENNETCTL_KEY_FILE")
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.is_file():
        return None
    token = p.read_text(encoding="utf-8").strip()
    return token or None


def load_config() -> Config:
    _enforce_env_contract()
    return Config(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://tennetctl:tennetctl_dev@localhost:5434/solsocial",
        ),
        app_port=int(os.environ.get("SOLSOCIAL_APP_PORT", str(_DEFAULT_PORT))),
        debug=os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes"),
        tennetctl_url=os.environ.get(
            "SOLSOCIAL_TENNETCTL_URL", "http://localhost:51734",
        ),
        tennetctl_service_api_key=_load_service_api_key(),
        application_code=os.environ.get("SOLSOCIAL_APPLICATION_CODE", "solsocial"),
        tennetctl_org_id=os.environ.get("SOLSOCIAL_TENNETCTL_ORG_ID"),
        frontend_origin=os.environ.get(
            "SOLSOCIAL_FRONTEND_ORIGIN", "http://localhost:51835",
        ),
        publisher_mode=os.environ.get("SOLSOCIAL_PUBLISHER_MODE", "stub"),
        linkedin=_load_provider("linkedin"),
        twitter=_load_provider("twitter"),
        instagram=_load_provider("instagram"),
    )
