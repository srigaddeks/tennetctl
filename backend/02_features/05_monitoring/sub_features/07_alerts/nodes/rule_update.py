"""monitoring.alerts.rule_update — update an alert rule."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class RuleUpdate(Node):
    key = "monitoring.alerts.rule_update"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        id: str
        name: str | None = None
        description: str | None = None
        dsl: dict[str, Any] | None = None
        condition: dict[str, Any] | None = None
        severity: str | None = None
        notify_template_key: str | None = None
        labels: dict[str, Any] | None = None
        is_active: bool | None = None
        paused_until: datetime | None = None

    class Output(BaseModel):
        id: str
        ok: bool

    async def run(
        self, ctx: Any, inputs: "RuleUpdate.Input",
    ) -> "RuleUpdate.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        row = await _service.update_rule(
            pool, conn, ctx,
            org_id=inputs.org_id, rule_id=inputs.id,
            name=inputs.name, description=inputs.description,
            dsl=inputs.dsl, condition=inputs.condition,
            severity=inputs.severity,
            notify_template_key=inputs.notify_template_key,
            labels=inputs.labels, is_active=inputs.is_active,
            paused_until=inputs.paused_until,
        )
        return self.Output(id=inputs.id, ok=row is not None)
