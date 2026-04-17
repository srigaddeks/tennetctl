"""monitoring.dashboards.delete — soft-delete a dashboard."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

Node = _catalog_node.Node


class DeleteDashboard(Node):
    key = "monitoring.dashboards.delete"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        user_id: str
        id: str

    class Output(BaseModel):
        deleted: bool

    async def run(
        self, ctx: Any, inputs: "DeleteDashboard.Input",
    ) -> "DeleteDashboard.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        ok = await _service.delete_dashboard(
            conn, ctx, pool,
            org_id=inputs.org_id, user_id=inputs.user_id, id=inputs.id,
        )
        return self.Output(deleted=ok)
