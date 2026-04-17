"""monitoring.alerts.rule_create — create an alert rule."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, Field

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class RuleCreate(Node):
    key = "monitoring.alerts.rule_create"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        name: str
        description: str | None = None
        target: str
        dsl: dict[str, Any]
        condition: dict[str, Any]
        severity: str
        notify_template_key: str
        labels: dict[str, Any] = Field(default_factory=dict)

    class Output(BaseModel):
        id: str

    async def run(
        self, ctx: Any, inputs: "RuleCreate.Input",
    ) -> "RuleCreate.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        row = await _service.create_rule(
            pool, conn, ctx,
            org_id=inputs.org_id,
            name=inputs.name,
            description=inputs.description,
            target=inputs.target,
            dsl=inputs.dsl,
            condition=inputs.condition,
            severity=inputs.severity,
            notify_template_key=inputs.notify_template_key,
            labels=inputs.labels,
        )
        return self.Output(id=str(row["id"]))
