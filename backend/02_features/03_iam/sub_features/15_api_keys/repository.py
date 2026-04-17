"""Repository for iam.api_keys — raw asyncpg. Reads v_iam_api_keys."""

from __future__ import annotations

from typing import Any

_FCT = '"03_iam"."28_fct_iam_api_keys"'
_VIEW = '"03_iam"."v_iam_api_keys"'


async def list_api_keys(conn: Any, *, org_id: str, user_id: str) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT * FROM {_VIEW} WHERE org_id = $1 AND user_id = $2 ORDER BY created_at DESC',
        org_id, user_id,
    )
    return [dict(r) for r in rows]


async def get_by_id(conn: Any, *, key_id: str) -> dict | None:
    row = await conn.fetchrow(f'SELECT * FROM {_VIEW} WHERE id = $1', key_id)
    return dict(row) if row else None


async def get_active_by_key_id(conn: Any, *, key_id: str) -> dict | None:
    """Used by the Bearer middleware. Includes secret_hash for argon2 verify."""
    row = await conn.fetchrow(
        f"""
        SELECT id, org_id, user_id, key_id, secret_hash, scopes,
               expires_at, revoked_at, is_active, deleted_at
        FROM {_FCT}
        WHERE key_id = $1
          AND deleted_at IS NULL
          AND revoked_at IS NULL
          AND is_active = TRUE
        """,
        key_id,
    )
    return dict(row) if row else None


async def insert_api_key(
    conn: Any,
    *,
    id: str,
    org_id: str,
    user_id: str,
    key_id: str,
    secret_hash: str,
    label: str,
    scopes: list[str],
    expires_at: Any,
    created_by: str,
) -> dict:
    await conn.execute(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, user_id, key_id, secret_hash, label, scopes,
             expires_at, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
        """,
        id, org_id, user_id, key_id, secret_hash, label, scopes, expires_at, created_by,
    )
    row = await conn.fetchrow(f'SELECT * FROM {_VIEW} WHERE id = $1', id)
    return dict(row)


async def revoke_api_key(conn: Any, *, key_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        f"""
        UPDATE {_FCT}
        SET revoked_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP,
            updated_by = $2
        WHERE id = $1 AND revoked_at IS NULL AND deleted_at IS NULL
        """,
        key_id, updated_by,
    )
    return result == "UPDATE 1"


async def touch_last_used(conn: Any, *, key_id: str) -> None:
    """Best-effort update — do not fail the caller if this errors."""
    try:
        await conn.execute(
            f'UPDATE {_FCT} SET last_used_at = CURRENT_TIMESTAMP WHERE key_id = $1',
            key_id,
        )
    except Exception:
        pass


async def get_raw_by_id(conn: Any, *, id: str) -> dict | None:
    """Fetch raw fct row including scopes for rotation."""
    row = await conn.fetchrow(
        f'SELECT id, org_id, user_id, key_id, scopes, label, expires_at, revoked_at, deleted_at '
        f'FROM {_FCT} WHERE id = $1',
        id,
    )
    return dict(row) if row else None
