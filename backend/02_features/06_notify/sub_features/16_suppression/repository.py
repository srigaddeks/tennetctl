"""Repository for notify.suppression."""

from __future__ import annotations

from typing import Any

_FCT = '"06_notify"."17_fct_notify_suppressions"'
_VIEW = '"06_notify"."v_notify_suppressions"'


async def list_suppressions(conn: Any, *, org_id: str, limit: int = 100) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT * FROM {_VIEW} WHERE org_id = $1 ORDER BY created_at DESC LIMIT $2',
        org_id, limit,
    )
    return [dict(r) for r in rows]


async def add_suppression(
    conn: Any,
    *,
    id: str,
    org_id: str,
    email: str,
    reason_code: str,
    created_by: str,
    delivery_id: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Insert or skip on conflict (org_id, email). Returns the row or None if dup."""
    await conn.execute(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, email, reason_code, delivery_id, notes, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (org_id, email) DO NOTHING
        """,
        id, org_id, email, reason_code, delivery_id, notes, created_by,
    )
    row = await conn.fetchrow(
        f'SELECT * FROM {_VIEW} WHERE org_id = $1 AND email = $2',
        org_id, email,
    )
    return dict(row) if row else None


async def remove_suppression(conn: Any, *, org_id: str, email: str) -> bool:
    result = await conn.execute(
        f'DELETE FROM {_FCT} WHERE org_id = $1 AND email = $2',
        org_id, email,
    )
    return result == "DELETE 1"


async def is_suppressed(conn: Any, *, org_id: str, email: str) -> bool:
    val = await conn.fetchval(
        f'SELECT 1 FROM {_FCT} WHERE org_id = $1 AND lower(email) = lower($2) LIMIT 1',
        org_id, email,
    )
    return val is not None


async def get_reason(conn: Any, *, org_id: str, email: str) -> str | None:
    val = await conn.fetchval(
        f'SELECT reason_code FROM {_FCT} WHERE org_id = $1 AND lower(email) = lower($2) LIMIT 1',
        org_id, email,
    )
    return val
