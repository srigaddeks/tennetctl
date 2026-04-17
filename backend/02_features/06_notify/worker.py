"""
Notify subscription worker.

Polls the audit outbox, matches active subscriptions by org + event_key_pattern,
and enqueues delivery rows for each match. Critical category templates fan out
to email + webpush + in_app simultaneously.

Worker state: cursor held in-memory (resets to latest outbox ID on process start,
so existing events are not re-processed on restart).

Usage (in app lifespan):
    task = start_worker(pool)
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_outbox_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.repository"
)
_sub_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.05_subscriptions.service"
)
_del_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)
_tmpl_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.repository"
)
_var_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.04_variables.repository"
)
_pref_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.service"
)

logger = logging.getLogger("notify.worker")

# Channels included in critical fan-out (email=1, webpush=2, in_app=3).
# SMS (id=4) is excluded from automatic fan-out in v0.1.
_CRITICAL_CHANNELS = [1, 2, 3]

# How long to sleep between polls when no NOTIFY arrives (fallback).
_POLL_INTERVAL_S = 30


async def process_audit_events(pool: Any, since_id: int) -> int:
    """
    Poll the audit outbox for events newer than `since_id`.
    For each event, match active subscriptions and create delivery rows.
    Returns the new cursor (last outbox_id processed, or `since_id` if nothing new).

    This function is synchronous-looking but fully async — safe to call from tests
    or from the worker loop without starting the background listener.
    """
    async with pool.acquire() as conn:
        subscriptions = await _sub_service.list_active_for_worker(conn)
        rows = await _outbox_repo.poll_outbox(conn, since_id=since_id, limit=100)
        if not rows:
            return since_id
        for event in rows:
            for sub in subscriptions:
                if sub["org_id"] != event["org_id"]:
                    continue
                if not _sub_service.matches_pattern(event["event_key"], sub["event_key_pattern"]):
                    continue
                await _enqueue_for_subscription(conn, sub, event)
        return rows[-1]["outbox_id"]


async def _enqueue_for_subscription(conn: Any, subscription: dict, audit_event: dict) -> None:
    """Create delivery row(s) for one matched subscription + audit event."""
    template = await _tmpl_repo.get_template(conn, template_id=subscription["template_id"])
    if template is None:
        logger.warning(
            "subscription %s references missing template %s — skipping",
            subscription["id"],
            subscription["template_id"],
        )
        return

    is_critical = template.get("category_code") == "critical"
    channels = _CRITICAL_CHANNELS if is_critical else [subscription["channel_id"]]

    context = {
        "actor_user_id": audit_event.get("actor_user_id"),
        "org_id": audit_event.get("org_id"),
        "workspace_id": audit_event.get("workspace_id"),
        "event_metadata": audit_event.get("metadata"),
    }
    resolved = await _var_repo.resolve_variables(
        conn, template_id=template["id"], context=context
    )

    priority_id = template.get("priority_id") or 2  # default: normal
    recipient_user_id = audit_event.get("actor_user_id") or ""
    audit_outbox_id = audit_event.get("outbox_id")

    org_id = subscription["org_id"]
    category_id = template.get("category_id") or 1  # default: transactional

    for channel_id in channels:
        # Skip delivery if user has opted out of this channel+category combo.
        # Critical category (id=2) is always delivered — is_opted_in returns True.
        if recipient_user_id:
            opted_in = await _pref_service.is_opted_in(
                conn,
                user_id=recipient_user_id,
                org_id=org_id,
                channel_id=channel_id,
                category_id=category_id,
            )
            if not opted_in:
                logger.debug(
                    "Skipping delivery for user %s: opted out of channel=%d category=%d",
                    recipient_user_id, channel_id, category_id,
                )
                continue

        await _del_service.create_delivery(
            conn,
            subscription_id=subscription["id"],
            org_id=org_id,
            template_id=template["id"],
            recipient_user_id=recipient_user_id,
            channel_id=channel_id,
            priority_id=priority_id,
            resolved_variables=resolved,
            audit_outbox_id=audit_outbox_id,
        )

    n = len(channels)
    logger.debug(
        "Enqueued %d delivery/ies for event %s (sub=%s, critical=%s)",
        n, audit_event.get("event_key"), subscription["id"], is_critical,
    )


async def _worker_loop(pool: Any) -> None:
    """
    Main loop: LISTEN on 'audit_events' for wake-up.
    Falls back to polling every _POLL_INTERVAL_S seconds.
    """
    async with pool.acquire() as conn:
        since_id = await _outbox_repo.latest_outbox_id(conn)
    logger.info("Notify subscription worker started (cursor=%d)", since_id)

    _wake = asyncio.Event()

    async def _on_notify(connection: Any, pid: int, channel: str, payload: str) -> None:
        _wake.set()

    listen_conn = await pool.acquire()
    try:
        await listen_conn.add_listener("audit_events", _on_notify)
        while True:
            try:
                await asyncio.wait_for(_wake.wait(), timeout=float(_POLL_INTERVAL_S))
            except asyncio.TimeoutError:
                pass
            _wake.clear()
            try:
                since_id = await process_audit_events(pool, since_id)
            except Exception:
                logger.exception("Error processing audit events (cursor=%d)", since_id)
    except asyncio.CancelledError:
        logger.info("Notify subscription worker stopped")
    finally:
        try:
            await listen_conn.remove_listener("audit_events", _on_notify)
        except Exception:
            pass
        await pool.release(listen_conn)


def start_worker(pool: Any) -> "asyncio.Task[None]":
    """
    Start the notify subscription worker as an asyncio background task.
    Call from the app lifespan after the pool is initialised.
    Cancel the returned task on shutdown.
    """
    return asyncio.create_task(_worker_loop(pool), name="notify-subscription-worker")
