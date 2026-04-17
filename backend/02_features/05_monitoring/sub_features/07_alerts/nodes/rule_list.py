"""monitoring.alerts.rule_list — list alert rules for the caller's org."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class RuleList(Node):
    key = "monitoring.alerts.rule_list"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        is_active: bool | None = None

    class Output(BaseModel):
        count: int

    async def run(
        self, ctx: Any, inputs: "RuleList.Input",
    ) -> "RuleList.Output":
        conn = ctx.conn
        rows = await _service.list_rules(
            conn, ctx, org_id=inputs.org_id, is_active=inputs.is_active,
        )
        return self.Output(count=len(rows))
