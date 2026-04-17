"""
notify.send.transactional — Effect node for direct transactional delivery.

Creates a delivery record immediately (bypassing the audit-outbox subscription
flow). Used by code paths that need to send a notification without a triggering
audit event. The worker picks up the delivery and sends it via the appropriate channel.

Emits: notify.send.transactional audit event.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module("backend.02_features.06_notify.sub_features.11_send.service")

Node = _catalog_node.Node


class SendTransactional(Node):
    key = "notify.send.transactional"
    kind = "effect"
    emits_audit = True
    config_schema: dict = {}
    input_schema: dict = {
        "type": "object",
        "required": ["org_id", "template_key", "recipient_user_id"],
        "properties": {
            "org_id": {"type": "string"},
            "template_key": {"type": "string"},
            "recipient_user_id": {"type": "string"},
            "channel_code": {"type": "string", "enum": ["email", "webpush", "in_app"], "default": "email"},
            "variables": {"type": "object"},
        },
    }
    output_schema: dict = {
        "type": "object",
        "required": ["delivery_id"],
        "properties": {
            "delivery_id": {"type": "string"},
        },
    }

    async def handler(self, ctx: Any, inputs: dict, config: dict) -> dict:
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        delivery_id = await _service.send_transactional(
            conn,
            pool,
            ctx,
            org_id=inputs["org_id"],
            template_key=inputs["template_key"],
            recipient_user_id=inputs["recipient_user_id"],
            channel_code=inputs.get("channel_code", "email"),
            variables=inputs.get("variables") or {},
        )
        return {"delivery_id": delivery_id}
