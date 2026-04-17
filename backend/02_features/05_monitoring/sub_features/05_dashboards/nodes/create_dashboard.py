"""monitoring.dashboards.create — create a dashboard."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

Node = _catalog_node.Node


class CreateDashboard(Node):
    key = "monitoring.dashboards.create"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        owner_user_id: str
        name: str
        description: str | None = None
        layout: dict[str, Any] | None = None
        shared: bool = False

    class Output(BaseModel):
        id: str

    async def run(
        self, ctx: Any, inputs: "CreateDashboard.Input",
    ) -> "CreateDashboard.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        row = await _service.create_dashboard(
            conn, ctx, pool,
            org_id=inputs.org_id,
            owner_user_id=inputs.owner_user_id,
            name=inputs.name,
            description=inputs.description,
            layout=inputs.layout,
            shared=inputs.shared,
        )
        return self.Output(id=str(row["id"]))
