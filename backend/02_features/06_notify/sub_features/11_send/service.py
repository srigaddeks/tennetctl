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
) -> str:
    _errors: Any = import_module("backend.01_core.errors")

    template = await _tmpl_repo.get_template_by_key(conn, org_id=org_id, key=template_key)
    if template is None:
        raise _errors.NotFoundError(f"template {template_key!r} not found for org {org_id!r}")

    channel_id = _CHANNEL_MAP.get(channel_code)
    if channel_id is None:
        raise _errors.ValidationError(f"unknown channel_code {channel_code!r}")

    resolved = await _var_service.resolve_variables(conn, template_id=template["id"], context={})
    resolved.update(variables)

    delivery = await _del_service.create_delivery(
        conn,
        subscription_id=None,
        org_id=org_id,
        template_id=template["id"],
        recipient_user_id=recipient_user_id,
        channel_id=channel_id,
        priority_id=template["priority_id"],
        resolved_variables=resolved,
    )
    delivery_id = delivery["id"] if delivery else None

    if delivery_id:
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
                },
            },
        )

    return delivery_id or ""
