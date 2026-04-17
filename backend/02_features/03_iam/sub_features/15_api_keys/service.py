"""Service for iam.api_keys.

Mints scoped machine-to-machine tokens of the form "nk_<key_id>.<secret>"
where key_id is a 12-char lowercase base32 prefix (public, indexed) and the
secret is 32 random bytes base64url-encoded. Secret is argon2id-hashed via
the shared credentials helper before storage; full token is returned to the
caller exactly once.

Used by:
  - iam.api_keys.routes — mint / list / revoke endpoints
  - backend.01_core.middleware — Bearer token validation
"""

from __future__ import annotations

import base64
import secrets
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_repo: Any = import_module("backend.02_features.03_iam.sub_features.15_api_keys.repository")
_core_id: Any = import_module("backend.01_core.id")
_credentials: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
_catalog: Any = import_module("backend.01_catalog")


_PREFIX = "nk_"


def _new_key_id() -> str:
    # 12 lowercase base32 chars = ~60 bits entropy. No padding.
    raw = secrets.token_bytes(8)
    return base64.b32encode(raw).decode("ascii").lower().rstrip("=")[:12]


def _new_secret() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def parse_token(token: str) -> tuple[str, str] | None:
    """Split "nk_<key_id>.<secret>" into (key_id, secret). Returns None if malformed."""
    if not token or not token.startswith(_PREFIX):
        return None
    body = token[len(_PREFIX):]
    if "." not in body:
        return None
    key_id, secret = body.split(".", 1)
    if not key_id or not secret:
        return None
    return key_id, secret


async def list_api_keys(conn: Any, *, org_id: str, user_id: str) -> list[dict]:
    return await _repo.list_api_keys(conn, org_id=org_id, user_id=user_id)


async def mint_api_key(
    conn: Any,
    pool: Any,
    ctx: Any,
    vault: Any,
    *,
    org_id: str,
    user_id: str,
    label: str,
    scopes: list[str],
    expires_at: Any = None,
) -> dict:
    """Create a key; return the sanitized row with `token` attached exactly once."""
    key_id = _new_key_id()
    secret = _new_secret()
    token = f"{_PREFIX}{key_id}.{secret}"

    secret_hash = await _credentials.hash_password(secret, vault)

    row = await _repo.insert_api_key(
        conn,
        id=_core_id.uuid7(),
        org_id=org_id,
        user_id=user_id,
        key_id=key_id,
        secret_hash=secret_hash,
        label=label,
        scopes=scopes,
        expires_at=expires_at,
        created_by=ctx.user_id or "system",
    )

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.api_keys.created",
            "outcome": "success",
            "metadata": {"key_id": key_id, "scopes": scopes, "label": label},
        },
    )

    row["token"] = token
    return row


async def revoke_api_key(
    conn: Any, pool: Any, ctx: Any, *, key_id: str,
) -> bool:
    deleted = await _repo.revoke_api_key(
        conn, key_id=key_id, updated_by=ctx.user_id or "system",
    )
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "iam.api_keys.revoked",
                "outcome": "success",
                "metadata": {"id": key_id},
            },
        )
    return deleted


async def validate_token(
    conn: Any, vault: Any, *, token: str,
) -> dict | None:
    """Look up + verify a Bearer token. Returns the key row on success, else None.

    Called from the Bearer-auth middleware. Does NOT raise — any failure
    returns None so the request proceeds unauthenticated.
    """
    parsed = parse_token(token)
    if parsed is None:
        return None
    key_id, secret = parsed

    row = await _repo.get_active_by_key_id(conn, key_id=key_id)
    if row is None:
        return None

    # Expiry check (naive UTC; DB stores TIMESTAMP without tz).
    exp = row.get("expires_at")
    if exp is not None and isinstance(exp, datetime) and exp < datetime.now(timezone.utc).replace(tzinfo=None):
        return None

    # argon2 verify against the stored hash. We re-peppered on create using
    # credentials.hash_password; verify must use the same pepper.
    try:
        peppered = await _credentials._peppered(secret, vault)
        _credentials._hasher.verify(row["secret_hash"], peppered)
    except Exception:
        return None

    return row
