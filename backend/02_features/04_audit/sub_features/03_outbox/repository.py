"""
audit.outbox — asyncpg repository.

Reads from 61_evt_audit_outbox JOIN v_audit_events for full event detail.
Consumers pass their last-seen outbox id as `since_id` (BIGINT cursor).
Returns rows with outbox_id so consumer can advance the cursor.
"""

from __future__ import annotations

from typing import Any

_OUTBOX = '"04_audit"."61_evt_audit_outbox"'
_VIEW   = '"04_audit"."v_audit_events"'


async def poll_outbox(
    conn: Any,
    *,
    since_id: int,
    limit: int = 50,
    org_id: str | None = None,
) -> list[dict]:
    """
    Return events from the outbox newer than `since_id`.
    Joins with v_audit_events for full event detail.
    Ordered by outbox.id ASC (oldest-first for consumers).
    org_id filters to a single tenant when provided.
    """
    params: list[Any] = [since_id, limit]
    org_clause = ""
    if org_id is not None:
        params.append(org_id)
        org_clause = f"AND e.org_id = ${len(params)}"

    sql = (
        f"SELECT o.id AS outbox_id, "
        f"       e.id, e.event_key, e.event_label, e.event_description, "
        f"       e.category_code, e.category_label, "
        f"       e.actor_user_id, e.actor_session_id, e.org_id, e.workspace_id, "
        f"       e.trace_id, e.span_id, e.parent_span_id, "
        f"       e.outcome, e.metadata, e.created_at "
        f"FROM {_OUTBOX} o "
        f"JOIN {_VIEW} e ON e.id = o.event_id "
        f"WHERE o.id > $1 {org_clause} "
        f"ORDER BY o.id ASC "
        f"LIMIT $2"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def latest_outbox_id(conn: Any) -> int:
    """Return the current max outbox id (0 if empty). Used to initialise cursors."""
    result = await conn.fetchval(
        f"SELECT COALESCE(MAX(id), 0) FROM {_OUTBOX}"
    )
    return int(result)
