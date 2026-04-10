"""kbio API key service.

Business logic for API key lifecycle: create, list, revoke, delete.
Generates raw keys with prefix, hashes with SHA-256 for storage.
"""

from __future__ import annotations

import hashlib
import secrets
import importlib
from typing import Any

import asyncpg

_repo = importlib.import_module("03_kbio.api_keys.repository")
_errors = importlib.import_module("01_core.errors")

_KEY_PREFIX = "kbio_"
_KEY_BYTE_LENGTH = 32


def _generate_raw_key() -> tuple[str, str, str]:
    """Generate a raw API key, its prefix, and SHA-256 hash.

    Returns (raw_key, prefix, key_hash).
    """
    random_part = secrets.token_urlsafe(_KEY_BYTE_LENGTH)
    raw_key = f"{_KEY_PREFIX}{random_part}"
    prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, prefix, key_hash


async def create_api_key(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    workspace_id: str,
    name: str,
    description: str = "",
    permissions: dict[str, Any] | None = None,
    rate_limit: str = "",
    expires_at: str = "",
    actor_id: str,
) -> dict[str, Any]:
    """Create a new API key. Returns the raw key (shown once)."""
    import uuid

    raw_key, prefix, key_hash = _generate_raw_key()
    key_id = str(uuid.uuid4())

    # status_id=1 = active
    await _repo.create_api_key(
        conn,
        key_id=key_id,
        org_id=org_id,
        workspace_id=workspace_id,
        key_prefix=prefix,
        key_hash=key_hash,
        status_id=1,
        actor_id=actor_id,
        attrs={
            "name": name,
            "description": description,
            "permissions": permissions or {},
            "rate_limit": rate_limit,
            "expires_at": expires_at,
        },
    )

    return {
        "id": key_id,
        "raw_key": raw_key,
        "key_prefix": prefix,
        "name": name,
    }


async def list_api_keys(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List API keys for an org."""
    items, total = await _repo.list_api_keys(conn, org_id=org_id, limit=limit, offset=offset)
    for item in items:
        item.pop("key_hash", None)
        item.pop("status_id", None)
        item.pop("is_deleted", None)
    return items, total


async def get_api_key(
    conn: asyncpg.Connection,
    key_id: str,
) -> dict[str, Any]:
    """Get a single API key."""
    row = await _repo.get_api_key(conn, key_id)
    if not row:
        raise _errors.AppError("NOT_FOUND", f"API key '{key_id}' not found.", 404)
    row.pop("key_hash", None)
    row.pop("status_id", None)
    row.pop("is_deleted", None)
    return row


async def update_api_key(
    conn: asyncpg.Connection,
    key_id: str,
    *,
    attrs: dict[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Update API key attributes."""
    existing = await _repo.get_api_key(conn, key_id)
    if not existing:
        raise _errors.AppError("NOT_FOUND", f"API key '{key_id}' not found.", 404)

    update_attrs = {k: v for k, v in attrs.items() if v is not None}
    if update_attrs:
        await _repo.update_api_key_attrs(conn, key_id=key_id, attrs=update_attrs, actor_id=actor_id)

    return await get_api_key(conn, key_id)


async def revoke_api_key(
    conn: asyncpg.Connection,
    key_id: str,
    *,
    actor_id: str,
) -> None:
    """Revoke an API key."""
    existing = await _repo.get_api_key(conn, key_id)
    if not existing:
        raise _errors.AppError("NOT_FOUND", f"API key '{key_id}' not found.", 404)
    if existing["status"] == "revoked":
        raise _errors.AppError("ALREADY_REVOKED", "API key is already revoked.", 409)

    # revoked status_id = 2
    await _repo.revoke_api_key(conn, key_id, revoked_status_id=2, actor_id=actor_id)


async def delete_api_key(
    conn: asyncpg.Connection,
    key_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete an API key."""
    existing = await _repo.get_api_key(conn, key_id)
    if not existing:
        raise _errors.AppError("NOT_FOUND", f"API key '{key_id}' not found.", 404)

    await _repo.soft_delete_api_key(conn, key_id, actor_id=actor_id)
