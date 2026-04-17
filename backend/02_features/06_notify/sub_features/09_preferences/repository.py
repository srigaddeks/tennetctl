"""Repository for notify.preferences — asyncpg raw SQL."""

from __future__ import annotations

from typing import Any

_FCT  = '"06_notify"."17_fct_notify_user_preferences"'
_VIEW = '"06_notify"."v_notify_user_preferences"'


async def list_preferences(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {_VIEW} WHERE user_id = $1 AND org_id = $2",
        user_id, org_id,
    )
    return [dict(r) for r in rows]


async def upsert_preference(
    conn: Any,
    *,
    pref_id: str,
    org_id: str,
    user_id: str,
    channel_id: int,
    category_id: int,
    is_opted_in: bool,
    updated_by: str,
) -> dict:
    await conn.execute(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, user_id, channel_id, category_id, is_opted_in,
             created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
        ON CONFLICT (org_id, user_id, channel_id, category_id)
        DO UPDATE SET
            is_opted_in = EXCLUDED.is_opted_in,
            updated_by  = EXCLUDED.updated_by,
            updated_at  = CURRENT_TIMESTAMP
        """,
        pref_id, org_id, user_id, channel_id, category_id, is_opted_in, updated_by,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {_VIEW} WHERE org_id=$1 AND user_id=$2 AND channel_id=$3 AND category_id=$4",
        org_id, user_id, channel_id, category_id,
    )
    return dict(row)


async def get_opt_in(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    channel_id: int,
    category_id: int,
) -> bool | None:
    """
    Returns stored is_opted_in, or None if no preference row exists.
    Callers should treat None as True (default opt-in).
    """
    row = await conn.fetchrow(
        f"""
        SELECT is_opted_in FROM {_FCT}
        WHERE org_id=$1 AND user_id=$2 AND channel_id=$3 AND category_id=$4
        """,
        org_id, user_id, channel_id, category_id,
    )
    return row["is_opted_in"] if row else None
