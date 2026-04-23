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
    deep_link: str | None = None,
    idempotency_key: str | None = None,
    scheduled_at: Any = None,
    application_id: str | None = None,
) -> dict | None:
    """Insert a delivery row. Returns None when the subscription-level idempotency
    guard (subscription_id, audit_outbox_id, channel_id) hits an existing row.

    When `idempotency_key` is provided, first checks for an existing row with
    the same (org_id, idempotency_key) and returns it as-is — Send API
    idempotency. This sidesteps the INSERT entirely so no wasted uuid7 is
    burned and callers always see the original row.
    """
    if idempotency_key is not None:
        existing = await conn.fetchrow(
            f"SELECT * FROM {_VIEW} WHERE org_id = $1 AND idempotency_key = $2",
            org_id, idempotency_key,
        )
        if existing is not None:
            return dict(existing)

    row = await conn.fetchrow(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, subscription_id, template_id, recipient_user_id,
             channel_id, priority_id, resolved_variables, audit_outbox_id,
             deep_link, idempotency_key, scheduled_at, application_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (subscription_id, audit_outbox_id, channel_id)
            WHERE subscription_id IS NOT NULL AND audit_outbox_id IS NOT NULL
        DO NOTHING
        RETURNING id
        """,
        delivery_id, org_id, subscription_id, template_id, recipient_user_id,
        channel_id, priority_id, resolved_variables, audit_outbox_id,
        deep_link, idempotency_key, scheduled_at, application_id,
    )
    if row is None:
        # Duplicate subscription/outbox/channel tuple.
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


async def mark_retryable_error(
    conn: Any,
    *,
    delivery_id: str,
    reason: str,
    backoff_seconds: int,
) -> dict:
    """Record a retryable send error.

    Increments attempt_count. If the new count reaches max_attempts, marks the
    delivery failed (status=8). Otherwise keeps status=queued and schedules
    the next attempt at NOW() + backoff_seconds.

    Returns the updated row from the view.
    """
    await conn.execute(
        f"""
        UPDATE {_FCT}
        SET attempt_count = attempt_count + 1,
            failure_reason = $2,
            status_id = CASE
                WHEN attempt_count + 1 >= max_attempts THEN 8  -- failed
                ELSE 2                                         -- queued (retry)
            END,
            next_retry_at = CASE
                WHEN attempt_count + 1 >= max_attempts THEN NULL
                ELSE CURRENT_TIMESTAMP + make_interval(secs => $3)
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        delivery_id, reason, backoff_seconds,
    )
    row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", delivery_id)
    return dict(row)


def backoff_seconds_for_attempt(attempt_count: int) -> int:
    """Exponential backoff: 60s, 120s, 240s, 480s, ..."""
    return 60 * (2 ** max(0, attempt_count))


async def requeue_delivery(
    conn: Any,
    *,
    delivery_id: str,
) -> dict | None:
    """Reset a delivery back to pending so the worker picks it up again.

    Only meaningful for deliveries in a terminal error state (failed, bounced).
    Clears failure_reason + next_retry_at; keeps attempt_count for audit but
    resets it to 0 so the worker gets a fresh budget.
    """
    await conn.execute(
        f"""
        UPDATE {_FCT}
        SET status_id = 1,                  -- pending
            failure_reason = NULL,
            next_retry_at = NULL,
            attempt_count = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        delivery_id,
    )
    return await get_delivery(conn, delivery_id)


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
