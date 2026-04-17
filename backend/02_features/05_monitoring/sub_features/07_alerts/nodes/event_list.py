"""monitoring.alerts.event_list — list alert events for the caller's org."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from pydantic import BaseModel, Field

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

Node = _catalog_node.Node


class EventList(Node):
    key = "monitoring.alerts.event_list"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        rule_id: str | None = None
        state: str | None = None
        severity: str | None = None
        since: datetime | None = None
        limit: int = Field(default=100, ge=1, le=1000)

    class Output(BaseModel):
        count: int

    async def run(
        self, ctx: Any, inputs: "EventList.Input",
    ) -> "EventList.Output":
        conn = ctx.conn
        rows = await _service.list_alert_events(
            conn, ctx,
            org_id=inputs.org_id, rule_id=inputs.rule_id,
            state=inputs.state, severity=inputs.severity,
            since=inputs.since, limit=inputs.limit,
        )
        return self.Output(count=len(rows))
