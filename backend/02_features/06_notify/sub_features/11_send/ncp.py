"""NCP (Notification Control Plane) adapter.

Thin delegate over ``11_send/service.py::send_transactional`` so workers and
other internal callers have a single import point named after the user-facing
concept ("NCP"). Keeping this module separate from ``service.py`` means the
HTTP route layer and the worker layer can evolve their own authz / audit
conventions without leaking into each other.

IMPORTANT: before a worker can call ``send_transactional`` end-to-end it has
to agree on a template_key. Today there is no shared convention for alert
escalation notifications - defining that (seeded template + variable
registry) is prerequisite to the ``escalation_worker`` call site being
un-commented.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_service = import_module("backend.02_features.06_notify.sub_features.11_send.service")


async def send_transactional(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    template_key: str,
    recipient_user_id: str,
    channel_code: str = "email",
    variables: dict[str, Any] | None = None,
    deep_link: str | None = None,
    idempotency_key: str | None = None,
    scheduled_at: Any = None,
) -> tuple[str, bool]:
    """Delegate to ``send_transactional``. Returns ``(delivery_id, was_new)``."""
    return await _service.send_transactional(
        conn,
        pool,
        ctx,
        org_id=org_id,
        template_key=template_key,
        recipient_user_id=recipient_user_id,
        channel_code=channel_code,
        variables=variables or {},
        deep_link=deep_link,
        idempotency_key=idempotency_key,
        scheduled_at=scheduled_at,
    )
