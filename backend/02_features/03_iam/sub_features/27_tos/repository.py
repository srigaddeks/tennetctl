"""iam.tos — asyncpg repository."""

from __future__ import annotations

from typing import Any

_TOS = '"03_iam"."48_fct_tos_versions"'
_ACCEPT = '"03_iam"."49_lnk_user_tos_acceptance"'


async def insert_version(
    conn: Any,
    *,
    id: str,
    version: str,
    title: str,
    body_markdown: str,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        f'INSERT INTO {_TOS} (id, version, title, body_markdown, created_by, updated_by) '
        f'VALUES ($1, $2, $3, $4, $5, $5) '
        f'RETURNING id, version, title, body_markdown, published_at, effective_at, created_at, updated_at',
        id, version, title, body_markdown, created_by,
    )
    return dict(row)


async def list_versions(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT id, version, title, body_markdown, published_at, effective_at, created_at, updated_at '
        f'FROM {_TOS} ORDER BY created_at DESC',
    )
    return [dict(r) for r in rows]


async def get_current_version(conn: Any) -> dict | None:
    """Return the most recent version where effective_at <= now."""
    row = await conn.fetchrow(
        f'SELECT id, version, title, body_markdown, published_at, effective_at, created_at, updated_at '
        f'FROM {_TOS} '
        f'WHERE effective_at IS NOT NULL AND effective_at <= CURRENT_TIMESTAMP '
        f'ORDER BY effective_at DESC LIMIT 1',
    )
    return dict(row) if row else None


async def mark_effective(conn: Any, *, version_id: str, effective_at: str, updated_by: str) -> dict | None:
    from datetime import datetime as _dt
    try:
        eff_dt = _dt.fromisoformat(effective_at.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        eff_dt = _dt.fromisoformat(effective_at)
    row = await conn.fetchrow(
        f'UPDATE {_TOS} SET published_at = COALESCE(published_at, CURRENT_TIMESTAMP), '
        f'    effective_at = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        f'WHERE id = $3 '
        f'RETURNING id, version, title, body_markdown, published_at, effective_at, created_at, updated_at',
        eff_dt, updated_by, version_id,
    )
    return dict(row) if row else None


async def has_accepted(conn: Any, *, user_id: str, version_id: str) -> bool:
    result = await conn.fetchval(
        f'SELECT 1 FROM {_ACCEPT} WHERE user_id = $1 AND version_id = $2',
        user_id, version_id,
    )
    return result is not None


async def insert_acceptance(
    conn: Any,
    *,
    id: str,
    user_id: str,
    version_id: str,
    ip_hash: str | None,
) -> dict:
    row = await conn.fetchrow(
        f'INSERT INTO {_ACCEPT} (id, user_id, version_id, ip_hash) '
        f'VALUES ($1, $2, $3, $4) '
        f'ON CONFLICT (user_id, version_id) DO NOTHING '
        f'RETURNING id, user_id, version_id, accepted_at',
        id, user_id, version_id, ip_hash,
    )
    return dict(row) if row else {}
