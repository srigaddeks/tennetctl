"""Repository for notify.deliveries — asyncpg raw SQL."""

from __future__ import annotations

from typing import Any

_VIEW = '"06_notify"."v_notify_deliveries"'
_FCT  = '"06_notify"."15_fct_notify_deliveries"'
_EVT  = '"06_notify"."61_evt_notify_delivery_events"'


async def list_deliveries(
    conn: Any,
    *,
    org_id: str,
    status_code: str | None = None,
    channel_code: str | None = None,
    recipient_user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [org_id, limit, offset]
    clauses = ["org_id = $1"]

    if status_code:
        params.append(status_code)
        clauses.append(f"status_code = ${len(params)}")
    if channel_code:
        params.append(channel_code)
        clauses.append(f"channel_code = ${len(params)}")
    if recipient_user_id:
        params.append(recipient_user_id)
        clauses.append(f"recipient_user_id = ${len(params)}")

    where = " AND ".join(clauses)
    rows = await conn.fetch(
        f"SELECT * FROM {_VIEW} WHERE {where} ORDER BY created_at DESC LIMIT $2 OFFSET $3",
        *params,
    )
    return [dict(r) for r in rows]


async def get_delivery(conn: Any, delivery_id: str) -> dict | None:
    row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", delivery_id)
    return dict(row) if row else None


async def create_delivery(
    conn: Any,
    *,
    delivery_id: str,
    org_id: str,
    subscription_id: str | None,
    template_id: str,
    recipient_user_id: str,
    channel_id: int,
    priority_id: int,
    resolved_variables: dict,
    audit_outbox_id: int | None = None,
    campaign_id: str | None = None,
) -> dict | None:
    """Insert a delivery row. Returns None if duplicate (idempotency guard)."""
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, subscription_id, campaign_id, template_id, recipient_user_id,
             channel_id, priority_id, resolved_variables, audit_outbox_id)
        VALUES ($1, $2, $3, $10, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (subscription_id, audit_outbox_id, channel_id)
            WHERE subscription_id IS NOT NULL AND audit_outbox_id IS NOT NULL
        DO NOTHING
        RETURNING id
        """,
        delivery_id, org_id, subscription_id, template_id, recipient_user_id,
        channel_id, priority_id, resolved_variables, audit_outbox_id, campaign_id,
    )
    if row is None:
        # Duplicate — already processed this (subscription, outbox_event) pair.
        return None
    view_row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", delivery_id)
    return dict(view_row)


async def update_delivery_status(
    conn: Any,
    *,
    delivery_id: str,
    status_id: int,
    failure_reason: str | None = None,
    attempted_at: Any = None,
    delivered_at: Any = None,
) -> dict | None:
    await conn.execute(
        f"""
        UPDATE {_FCT}
        SET status_id = $2,
            failure_reason = COALESCE($3, failure_reason),
            attempted_at = COALESCE($4, attempted_at),
            delivered_at = COALESCE($5, delivered_at),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        delivery_id, status_id, failure_reason, attempted_at, delivered_at,
    )
    return await get_delivery(conn, delivery_id)


async def campaign_stats(conn: Any, *, campaign_id: str) -> dict:
    """Return delivery counts grouped by status_code for a campaign."""
    rows = await conn.fetch(
        f"""
        SELECT status_code, COUNT(*) AS cnt
        FROM {_VIEW}
        WHERE campaign_id = $1
        GROUP BY status_code
        """,
        campaign_id,
    )
    counts: dict[str, int] = {r["status_code"]: r["cnt"] for r in rows}
    total = sum(counts.values())
    return {"total": total, "by_status": counts}


async def create_delivery_event(
    conn: Any,
    *,
    event_id: str,
    delivery_id: str,
    event_type: str,
    metadata: dict | None = None,
) -> dict:
    await conn.execute(
        f"""
        INSERT INTO {_EVT} (id, delivery_id, event_type, metadata)
        VALUES ($1, $2, $3, $4)
        """,
        event_id, delivery_id, event_type, metadata or {},
    )
    row = await conn.fetchrow(
        f"SELECT * FROM \"06_notify\".\"v_notify_delivery_events\" WHERE id = $1", event_id
    )
    return dict(row)
