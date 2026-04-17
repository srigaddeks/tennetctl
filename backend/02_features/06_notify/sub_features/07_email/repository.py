"""Repository for notify.email — poll + claim queued email deliveries."""

from __future__ import annotations

from typing import Any

_FCT = '"06_notify"."15_fct_notify_deliveries"'
_VIEW = '"06_notify"."v_notify_deliveries"'


async def poll_and_claim_email_deliveries(conn: Any, *, limit: int = 10) -> list[dict]:
    """
    Atomically claim up to `limit` queued email deliveries (status=queued, channel=email).
    Sets attempted_at to prevent double-processing.
    Returns full view rows for claimed deliveries.
    """
    id_rows = await conn.fetch(
        f"""
        UPDATE {_FCT}
        SET attempted_at = CURRENT_TIMESTAMP,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id IN (
            SELECT id FROM {_FCT}
            WHERE status_id  = 2        -- queued
              AND channel_id = 1        -- email
              AND attempted_at IS NULL
            ORDER BY created_at ASC
            LIMIT $1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id
        """,
        limit,
    )
    if not id_rows:
        return []

    ids = [r["id"] for r in id_rows]
    rows = await conn.fetch(
        f"SELECT * FROM {_VIEW} WHERE id = ANY($1::text[])",
        ids,
    )
    return [dict(r) for r in rows]
