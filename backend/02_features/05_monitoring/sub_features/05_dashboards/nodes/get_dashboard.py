"""monitoring.dashboards.get — read a dashboard."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

Node = _catalog_node.Node


class GetDashboard(Node):
    key = "monitoring.dashboards.get"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        user_id: str
        id: str

    class Output(BaseModel):
        found: bool
        dashboard: dict[str, Any] | None = None

    async def run(
        self, ctx: Any, inputs: "GetDashboard.Input",
    ) -> "GetDashboard.Output":
        conn = ctx.conn
        row = await _service.get_dashboard(
            conn, org_id=inputs.org_id, user_id=inputs.user_id, id=inputs.id,
        )
        return self.Output(found=row is not None, dashboard=row)
