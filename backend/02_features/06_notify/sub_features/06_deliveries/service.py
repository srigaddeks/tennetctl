"""Service layer for notify.deliveries."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_core_id: Any = import_module("backend.01_core.id")

# Statuses that may be manually retried from the admin UI.
_RETRYABLE_STATUSES = {"failed", "bounced"}


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
    return await _repo.list_deliveries(
        conn,
        org_id=org_id,
        status_code=status_code,
        channel_code=channel_code,
        recipient_user_id=recipient_user_id,
        limit=limit,
        offset=offset,
    )


async def get_delivery(conn: Any, *, delivery_id: str) -> dict | None:
    return await _repo.get_delivery(conn, delivery_id)


# Channel id → shared constant with worker. In-app is the "always visible in bell"
# channel: rows are created and immediately advanced to status=delivered since the
# DB row IS the delivery (no async send step). Frontend unread state derives from
# whether the row has been marked "opened" by the user.
_IN_APP_CHANNEL_ID = 3
_STATUS_DELIVERED = 4


async def create_delivery(
    conn: Any,
    *,
    subscription_id: str | None,
    org_id: str,
    template_id: str,
    recipient_user_id: str,
    channel_id: int,
    priority_id: int,
    resolved_variables: dict,
    audit_outbox_id: int | None = None,
    deep_link: str | None = None,
    idempotency_key: str | None = None,
    scheduled_at: Any = None,
) -> dict | None:
    """
    Internal — called by the worker and the transactional API. No audit emit.
    Returns None if a delivery for this (subscription, outbox_event) already exists (idempotent).
    In-app deliveries (channel_id=3) auto-advance to status=delivered on creation.

    `deep_link` is the canonical URL the recipient should land on when they
    open the notification. If omitted, falls back to resolved_variables['url'].
    """
    if deep_link is None:
        deep_link = resolved_variables.get("url") or resolved_variables.get("deep_link")

    delivery_id = _core_id.uuid7()
    row = await _repo.create_delivery(
        conn,
        delivery_id=delivery_id,
        org_id=org_id,
        subscription_id=subscription_id,
        template_id=template_id,
        recipient_user_id=recipient_user_id,
        channel_id=channel_id,
        priority_id=priority_id,
        resolved_variables=resolved_variables,
        audit_outbox_id=audit_outbox_id,
        deep_link=deep_link,
        idempotency_key=idempotency_key,
        scheduled_at=scheduled_at,
    )
    # Dedup hit: an existing row was returned instead of a new insert.
    if row is not None and row["id"] != delivery_id:
        return row
    # In-app auto-advance to 'delivered' only when eligible now. A future
    # scheduled_at means the delivery waits until the scheduled time (the
    # bell poll filter on status=delivered+queued picks it up naturally).
    if row is not None and channel_id == _IN_APP_CHANNEL_ID:
        import datetime as _dt
        ready = scheduled_at is None or (
            isinstance(scheduled_at, _dt.datetime)
            and scheduled_at <= _dt.datetime.utcnow()
        )
        if ready:
            row = await _repo.update_delivery_status(
                conn, delivery_id=row["id"], status_id=_STATUS_DELIVERED,
            ) or row
    return row


async def unread_count(
    conn: Any,
    *,
    org_id: str,
    recipient_user_id: str,
) -> int:
    """Return count of unread deliveries for a user across all channels.

    Unread = status NOT IN (opened, clicked, failed, unsubscribed, bounced).
    Used by the bell badge to avoid fetching the full delivery list.
    """
    val = await conn.fetchval(
        '''
        SELECT COUNT(*) FROM "06_notify"."v_notify_deliveries"
        WHERE org_id = $1
          AND recipient_user_id = $2
          AND status_code NOT IN ('opened', 'clicked', 'failed', 'unsubscribed', 'bounced')
        ''',
        org_id, recipient_user_id,
    )
    return int(val or 0)


async def retry_delivery(
    conn: Any, *, delivery_id: str, org_id: str,
) -> dict:
    """Requeue a failed / bounced delivery.

    Raises:
      NotFoundError — delivery not found or not in caller's org
      ValidationError — delivery is not in a retryable state
    """
    _errors: Any = import_module("backend.01_core.errors")
    row = await _repo.get_delivery(conn, delivery_id)
    if row is None or row.get("org_id") != org_id:
        raise _errors.NotFoundError(f"delivery {delivery_id!r} not found")
    if row.get("status_code") not in _RETRYABLE_STATUSES:
        raise _errors.ValidationError(
            f"delivery status {row.get('status_code')!r} is not retryable "
            f"(only failed / bounced can be requeued)"
        )
    updated = await _repo.requeue_delivery(conn, delivery_id=delivery_id)
    return updated or row


async def update_delivery_status(
    conn: Any,
    *,
    delivery_id: str,
    status_id: int,
    failure_reason: str | None = None,
    attempted_at: Any = None,
    delivered_at: Any = None,
) -> dict | None:
    """Called by channel workers (11-04/05/06) to advance delivery status."""
    return await _repo.update_delivery_status(
        conn,
        delivery_id=delivery_id,
        status_id=status_id,
        failure_reason=failure_reason,
        attempted_at=attempted_at,
        delivered_at=delivered_at,
    )


async def mark_read(conn: Any, *, delivery_id: str, user_id: str) -> dict:
    """Mark a delivery as read (status → opened), across any channel.

    In-app: user clicking the bell item.
    Email:  pytracking already flips status when the pixel loads, but a user
            coming back to the app after reading the email can also mark it
            via this endpoint so the bell clears.
    WebPush: same — clicking the browser push notification can mark it read.

    Creates a delivery 'open' event. Idempotent: already-opened/clicked
    deliveries return their current state without creating a duplicate event.

    Raises:
      NotFoundError  — delivery_id not found
      ForbiddenError  — caller is not the recipient
    """
    _errors: Any = import_module("backend.01_core.errors")

    delivery = await _repo.get_delivery(conn, delivery_id)
    if delivery is None:
        raise _errors.NotFoundError(f"delivery {delivery_id!r} not found")
    if delivery.get("recipient_user_id") != user_id:
        raise _errors.ForbiddenError("not authorized to mark this delivery as read")

    # Idempotent: already opened/clicked → return as-is
    if delivery.get("status_id", 0) >= 5:
        return delivery

    event_id = _core_id.uuid7()
    await _repo.create_delivery_event(
        conn,
        event_id=event_id,
        delivery_id=delivery_id,
        event_type="open",
        metadata={"channel_code": delivery.get("channel_code")},
    )
    updated = await _repo.update_delivery_status(
        conn, delivery_id=delivery_id, status_id=5  # opened
    )
    return updated or delivery


# Back-compat alias — existing tests + callers use this name. New code should
# use mark_read directly.
mark_in_app_read = mark_read
