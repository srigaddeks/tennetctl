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

# In-app channel id — always fanned out alongside the subscribed channel so the
# notification bell shows every event the user would have received on any channel,
# regardless of browser push or email opt-in. Users can opt out per-category in
# preferences; the is_opted_in check below still applies.
_IN_APP_CHANNEL_ID = 3

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


async def _resolve_recipients(
    conn: Any, subscription: dict, audit_event: dict,
) -> list[str]:
    """Return the list of user_ids that should receive this delivery.

    actor — the user who triggered the event (self-service default).
    users — explicit recipient_filter.user_ids.
    roles — all active org users holding one of recipient_filter.role_codes.
    """
    mode = subscription.get("recipient_mode") or "actor"
    flt = subscription.get("recipient_filter") or {}
    org_id = audit_event.get("org_id")

    if mode == "actor":
        actor = audit_event.get("actor_user_id")
        return [actor] if actor else []

    if mode == "users":
        ids = flt.get("user_ids") or []
        return [uid for uid in ids if isinstance(uid, str) and uid]

    if mode == "roles":
        codes = flt.get("role_codes") or []
        if not codes or not org_id:
            return []
        rows = await conn.fetch(
            '''
            SELECT DISTINCT lnk.user_id
            FROM "03_iam"."42_lnk_user_roles" lnk
            JOIN "03_iam"."v_roles" r ON r.id = lnk.role_id
            WHERE lnk.org_id = $1 AND r.code = ANY($2::text[])
            ''',
            org_id, codes,
        )
        return [r["user_id"] for r in rows]

    return []


def _safe_deep_link(raw: str | None) -> str | None:
    """Restrict deep_link to path-only URLs (start with /) to prevent open redirects."""
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("/") and not raw.startswith("//"):
        return raw
    return None


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
    if is_critical:
        channels = list(_CRITICAL_CHANNELS)
    else:
        # Subscribed channel + always-on in-app (deduped). User can still opt out
        # of in-app per-category via preferences; is_opted_in enforces that below.
        channels = list(dict.fromkeys([subscription["channel_id"], _IN_APP_CHANNEL_ID]))

    context = {
        "actor_user_id": audit_event.get("actor_user_id"),
        "org_id": audit_event.get("org_id"),
        "workspace_id": audit_event.get("workspace_id"),
        "event_metadata": audit_event.get("metadata"),
    }
    resolved = await _var_repo.resolve_variables(
        conn, template_id=template["id"], context=context
    )
    # Propagate template subject as a first-class field so the bell / web push
    # / email subject all default to something meaningful instead of "Notification".
    resolved.setdefault("subject", template.get("subject") or "")
    resolved.setdefault("title", template.get("subject") or "")

    # Per-channel bodies on the template. The `bodies` field on v_notify_templates
    # is a JSON array of {channel_id, body_html, body_text, preheader}; pick one
    # by channel at send time (below).
    bodies_by_channel: dict[int, dict] = {}
    for b in (template.get("bodies") or []):
        if isinstance(b, dict) and b.get("channel_id"):
            bodies_by_channel[int(b["channel_id"])] = b

    priority_id = template.get("priority_id") or 2  # default: normal
    audit_outbox_id = audit_event.get("outbox_id")
    org_id = subscription["org_id"]
    category_id = template.get("category_id") or 1  # default: transactional

    # Resolve the recipient set from subscription.recipient_mode.
    recipients = await _resolve_recipients(conn, subscription, audit_event)
    if not recipients:
        logger.debug(
            "No recipients resolved for subscription %s (mode=%s)",
            subscription["id"], subscription.get("recipient_mode"),
        )
        return

    # Deep link: caller can stash a path under resolved_variables["url"] or
    # ["deep_link"]; enforce path-only for safety.
    deep_link = _safe_deep_link(resolved.get("url") or resolved.get("deep_link"))

    for recipient_user_id in recipients:
        for channel_id in channels:
            # Skip delivery if user has opted out of this channel+category combo.
            # Critical category (id=2) is always delivered — is_opted_in returns True.
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

            # Merge the channel-specific body into resolved_variables for this
            # delivery so rendering + in-app display have canonical fields.
            body = bodies_by_channel.get(channel_id)
            per_delivery_vars = dict(resolved)
            if body:
                if body.get("body_html"):
                    per_delivery_vars.setdefault("body_html", body["body_html"])
                if body.get("body_text"):
                    per_delivery_vars.setdefault("body", body["body_text"])
                    per_delivery_vars.setdefault("message", body["body_text"])
                if body.get("preheader"):
                    per_delivery_vars.setdefault("preheader", body["preheader"])

            await _del_service.create_delivery(
                conn,
                subscription_id=subscription["id"],
                org_id=org_id,
                template_id=template["id"],
                recipient_user_id=recipient_user_id,
                channel_id=channel_id,
                priority_id=priority_id,
                resolved_variables=per_delivery_vars,
                audit_outbox_id=audit_outbox_id,
                deep_link=deep_link,
            )

    logger.debug(
        "Enqueued deliveries for event %s (sub=%s, recipients=%d, channels=%d, critical=%s)",
        audit_event.get("event_key"), subscription["id"],
        len(recipients), len(channels), is_critical,
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
