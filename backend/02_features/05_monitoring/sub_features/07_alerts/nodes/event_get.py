"""monitoring.alerts.event_get — fetch one alert event by id + started_at."""

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


class EventGet(Node):
    key = "monitoring.alerts.event_get"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        id: str
        started_at: datetime

    class Output(BaseModel):
        id: str | None
        found: bool
        state: str | None = None

    async def run(
        self, ctx: Any, inputs: "EventGet.Input",
    ) -> "EventGet.Output":
        conn = ctx.conn
        row = await _service.get_alert_event(
            conn, ctx,
            org_id=inputs.org_id,
            event_id=inputs.id,
            started_at=inputs.started_at,
        )
        return self.Output(
            id=str(row["id"]) if row else None,
            found=row is not None,
            state=row["state"] if row else None,
        )
