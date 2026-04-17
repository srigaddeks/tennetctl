"""Service layer for notify.deliveries."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_core_id: Any = import_module("backend.01_core.id")


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
    campaign_id: str | None = None,
) -> dict | None:
    """
    Internal — called by the worker and the transactional API (Plan 11-10). No audit emit.
    Returns None if a delivery for this (subscription, outbox_event) already exists (idempotent).
    """
    delivery_id = _core_id.uuid7()
    return await _repo.create_delivery(
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
        campaign_id=campaign_id,
    )


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


async def mark_in_app_read(conn: Any, *, delivery_id: str, user_id: str) -> dict:
    """Mark an in-app delivery as read (status → opened).

    Creates a delivery 'open' event. Idempotent: already-opened deliveries
    return their current state without creating a duplicate event.

    Raises:
      NotFoundError  — delivery_id not found
      ValidationError — delivery is not channel=in_app
      ForbiddenError  — caller is not the recipient
    """
    _errors: Any = import_module("backend.01_core.errors")

    delivery = await _repo.get_delivery(conn, delivery_id)
    if delivery is None:
        raise _errors.NotFoundError(f"delivery {delivery_id!r} not found")
    if delivery.get("channel_code") != "in_app":
        raise _errors.ValidationError(
            "mark-read is only supported for in-app deliveries"
        )
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
        metadata={},
    )
    updated = await _repo.update_delivery_status(
        conn, delivery_id=delivery_id, status_id=5  # opened
    )
    return updated or delivery
