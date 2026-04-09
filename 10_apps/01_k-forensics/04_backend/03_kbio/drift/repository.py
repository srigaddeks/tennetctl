"""kbio drift repository.

All reads query v_sessions and v_score_events views in the 10_kbio schema.
No business logic — pure data access.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def get_session_drift(
    conn: asyncpg.Connection, sdk_session_id: str
) -> dict[str, Any] | None:
    """Fetch current session drift state from the sessions view.

    Returns the row as a plain dict, or None if the session does not exist.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_sessions WHERE sdk_session_id = $1',
        sdk_session_id,
    )
    return dict(row) if row else None


async def get_recent_score_events(
    conn: asyncpg.Connection,
    session_id: str,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fetch the most recent score events for a session, newest first.

    Used to derive drift trends over the last N pulses.
    """
    rows = await conn.fetch(
        """SELECT * FROM "10_kbio".v_score_events
           WHERE session_id = $1
           ORDER BY created_at DESC LIMIT $2""",
        session_id,
        limit,
    )
    return [dict(r) for r in rows]
