"""monitoring.alerts.rule_delete — soft-delete an alert rule."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class RuleDelete(Node):
    key = "monitoring.alerts.rule_delete"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        id: str

    class Output(BaseModel):
        ok: bool

    async def run(
        self, ctx: Any, inputs: "RuleDelete.Input",
    ) -> "RuleDelete.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        ok = await _service.delete_rule(
            pool, conn, ctx, org_id=inputs.org_id, rule_id=inputs.id,
        )
        return self.Output(ok=ok)
