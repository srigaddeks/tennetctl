"""monitoring.alerts.rule_get — fetch an alert rule."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class RuleGet(Node):
    key = "monitoring.alerts.rule_get"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        id: str

    class Output(BaseModel):
        id: str | None
        found: bool

    async def run(
        self, ctx: Any, inputs: "RuleGet.Input",
    ) -> "RuleGet.Output":
        conn = ctx.conn
        row = await _service.get_rule(
            conn, ctx, org_id=inputs.org_id, rule_id=inputs.id,
        )
        return self.Output(
            id=str(row["id"]) if row else None,
            found=row is not None,
        )
