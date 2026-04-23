"""Service for notify.send — pure transactional delivery creation."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_tmpl_repo: Any = import_module("backend.02_features.06_notify.sub_features.03_templates.repository")
_var_service: Any = import_module("backend.02_features.06_notify.sub_features.04_variables.service")
_del_service: Any = import_module("backend.02_features.06_notify.sub_features.06_deliveries.service")
_catalog: Any = import_module("backend.01_catalog")

_CHANNEL_MAP = {"email": 1, "webpush": 2, "in_app": 3}


async def send_transactional(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    template_key: str,
    recipient_user_id: str,
    channel_code: str,
    variables: dict,
    deep_link: str | None = None,
    idempotency_key: str | None = None,
    scheduled_at: Any = None,
    application_id: str | None = None,
) -> tuple[str, bool]:
    """Create a transactional delivery. Returns (delivery_id, was_new).

    was_new=False means the Idempotency-Key matched an existing row and no new
    delivery was created; callers should skip audit emission in that case.
    """
    _errors: Any = import_module("backend.01_core.errors")

    template = await _tmpl_repo.get_template_by_key(conn, org_id=org_id, key=template_key)
    if template is None:
        raise _errors.NotFoundError(f"template {template_key!r} not found for org {org_id!r}")

    channel_id = _CHANNEL_MAP.get(channel_code)
    if channel_id is None:
        raise _errors.ValidationError(f"unknown channel_code {channel_code!r}")

    # Suppression check for email channel only. recipient_user_id may be
    # an email address directly (transactional API accepts both).
    if channel_code == "email" and "@" in recipient_user_id:
        _suppression_repo = import_module(
            "backend.02_features.06_notify.sub_features.16_suppression.repository"
        )
        if await _suppression_repo.is_suppressed(
            conn, org_id=org_id, email=recipient_user_id,
        ):
            raise _errors.ValidationError(
                f"recipient {recipient_user_id!r} is in the suppression list"
            )

    resolved = await _var_service.resolve_variables(conn, template_id=template["id"], context={})
    resolved.update(variables)

    # Snapshot the row count so we can tell "new insert" vs "idempotency dedup".
    pre_count: int = 0
    if idempotency_key is not None:
        pre_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "06_notify"."15_fct_notify_deliveries" '
            'WHERE org_id = $1 AND idempotency_key = $2',
            org_id, idempotency_key,
        ) or 0

    delivery = await _del_service.create_delivery(
        conn,
        subscription_id=None,
        org_id=org_id,
        application_id=application_id,
        template_id=template["id"],
        recipient_user_id=recipient_user_id,
        channel_id=channel_id,
        priority_id=template["priority_id"],
        resolved_variables=resolved,
        deep_link=deep_link,
        idempotency_key=idempotency_key,
        scheduled_at=scheduled_at,
    )
    delivery_id: str = delivery["id"] if delivery else ""
    was_new = delivery is not None and (idempotency_key is None or pre_count == 0)

    if delivery_id and was_new:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "notify.send.transactional",
                "outcome": "success",
                "metadata": {
                    "template_key": template_key,
                    "recipient_user_id": recipient_user_id,
                    "channel_code": channel_code,
                    "delivery_id": delivery_id,
                    "idempotency_key": idempotency_key,
                },
            },
        )

    # Fan out fallback chain. Each step becomes a scheduled delivery at
    # now + wait_seconds on a different channel. Senders skip the fallback
    # if the primary reaches 'opened'/'clicked' before the scheduled time.
    if delivery_id and was_new:
        from datetime import datetime, timedelta
        _inv_channel = {v: k for k, v in _CHANNEL_MAP.items()}
        for step in (template.get("fallback_chain") or []):
            try:
                fb_channel_id = int(step.get("channel_id"))
                fb_wait = int(step.get("wait_seconds") or 0)
            except (TypeError, ValueError):
                continue
            if fb_channel_id == channel_id:
                continue  # don't re-send on the same channel
            if fb_channel_id not in _inv_channel:
                continue
            fb_sched = datetime.utcnow() + timedelta(seconds=fb_wait)
            fb_idem = f"{idempotency_key}-fb{fb_channel_id}" if idempotency_key else None
            await _del_service.create_delivery(
                conn,
                subscription_id=None,
                org_id=org_id,
                template_id=template["id"],
                recipient_user_id=recipient_user_id,
                channel_id=fb_channel_id,
                priority_id=template["priority_id"],
                resolved_variables=resolved,
                deep_link=deep_link,
                idempotency_key=fb_idem,
                scheduled_at=fb_sched,
            )

    return delivery_id, was_new
