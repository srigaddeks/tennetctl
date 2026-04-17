"""monitoring.dashboards.update — update a dashboard."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

Node = _catalog_node.Node


class UpdateDashboard(Node):
    key = "monitoring.dashboards.update"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        user_id: str
        id: str
        name: str | None = None
        description: str | None = None
        layout: dict[str, Any] | None = None
        shared: bool | None = None
        is_active: bool | None = None

    class Output(BaseModel):
        id: str
        updated: bool

    async def run(
        self, ctx: Any, inputs: "UpdateDashboard.Input",
    ) -> "UpdateDashboard.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        row = await _service.update_dashboard(
            conn, ctx, pool,
            org_id=inputs.org_id, user_id=inputs.user_id, id=inputs.id,
            name=inputs.name, description=inputs.description,
            layout=inputs.layout, shared=inputs.shared, is_active=inputs.is_active,
        )
        return self.Output(id=inputs.id, updated=row is not None)
