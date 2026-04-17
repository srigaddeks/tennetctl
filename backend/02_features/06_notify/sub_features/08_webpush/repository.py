"""
notify.webpush — repository layer.

Reads from view: v_notify_webpush_subscriptions
Writes to table: 16_fct_notify_webpush_subscriptions
"""

from __future__ import annotations

from typing import Any

_FCT = '"06_notify"."16_fct_notify_webpush_subscriptions"'
_VIEW = '"06_notify"."v_notify_webpush_subscriptions"'
_DELIVERIES_FCT = '"06_notify"."15_fct_notify_deliveries"'
_DELIVERIES_VIEW = '"06_notify"."v_notify_deliveries"'


async def list_subscriptions(conn: Any, *, user_id: str) -> list[dict]:
    """Return all active webpush subscriptions for a user."""
    rows = await conn.fetch(f"SELECT * FROM {_VIEW} WHERE user_id = $1", user_id)
    return [dict(r) for r in rows]


async def get_subscription(conn: Any, *, sub_id: str) -> dict | None:
    """Return a single subscription by ID (active only)."""
    row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", sub_id)
    return dict(row) if row else None


async def get_subscription_by_endpoint(conn: Any, *, endpoint: str) -> dict | None:
    """Return an active subscription matching the given endpoint URL."""
    row = await conn.fetchrow(
        f"SELECT * FROM {_FCT} WHERE endpoint = $1 AND deleted_at IS NULL", endpoint
    )
    return dict(row) if row else None


async def upsert_subscription(
    conn: Any,
    *,
    id: str,
    org_id: str,
    user_id: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    device_label: str | None,
    created_by: str,
) -> dict:
    """Insert or update a browser push subscription keyed on endpoint.

    If the endpoint already exists (for any user), update the keys + label
    and reactivate if soft-deleted. Returns the final row from the fct table.
    """
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, user_id, endpoint, p256dh, auth,
             device_label, is_active, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE, $8, $8)
        ON CONFLICT (endpoint) DO UPDATE
            SET p256dh       = EXCLUDED.p256dh,
                auth         = EXCLUDED.auth,
                device_label = COALESCE(EXCLUDED.device_label, {_FCT}.device_label),
                is_active    = TRUE,
                deleted_at   = NULL,
                updated_by   = EXCLUDED.updated_by,
                updated_at   = CURRENT_TIMESTAMP
        RETURNING *
        """,
        id, org_id, user_id, endpoint, p256dh, auth, device_label, created_by,
    )
    return dict(row)


async def soft_delete_subscription(
    conn: Any, *, sub_id: str, updated_by: str
) -> bool:
    """Soft-delete a subscription. Returns True if a row was actually deleted."""
    result = await conn.execute(
        f"""
        UPDATE {_FCT}
        SET deleted_at = CURRENT_TIMESTAMP,
            updated_by = $2,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND deleted_at IS NULL
        """,
        sub_id,
        updated_by,
    )
    return result == "UPDATE 1"


async def poll_and_claim_webpush_deliveries(
    conn: Any, *, limit: int = 10
) -> list[dict]:
    """Atomically claim queued webpush deliveries.

    Uses FOR UPDATE SKIP LOCKED so multiple workers do not double-process.
    Returns full view rows for all claimed deliveries.
    """
    id_rows = await conn.fetch(
        f"""
        UPDATE {_DELIVERIES_FCT}
        SET attempted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id IN (
            SELECT id FROM {_DELIVERIES_FCT}
            WHERE status_id = 2 AND channel_id = 2 AND attempted_at IS NULL
            ORDER BY created_at ASC LIMIT $1
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
        f"SELECT * FROM {_DELIVERIES_VIEW} WHERE id = ANY($1::text[])", ids
    )
    return [dict(r) for r in rows]


async def get_user_webpush_subscriptions(
    conn: Any, *, user_id: str
) -> list[dict]:
    """Return all active webpush subscriptions for a recipient user."""
    rows = await conn.fetch(f"SELECT * FROM {_VIEW} WHERE user_id = $1", user_id)
    return [dict(r) for r in rows]


async def mark_delivery_sent(conn: Any, *, delivery_id: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_DELIVERIES_FCT}
        SET status_id    = 3,
            delivered_at = CURRENT_TIMESTAMP,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        delivery_id,
    )


async def mark_delivery_failed(
    conn: Any, *, delivery_id: str, reason: str
) -> None:
    await conn.execute(
        f"""
        UPDATE {_DELIVERIES_FCT}
        SET status_id      = 8,
            failure_reason = $2,
            updated_at     = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        delivery_id,
        reason[:500],
    )
