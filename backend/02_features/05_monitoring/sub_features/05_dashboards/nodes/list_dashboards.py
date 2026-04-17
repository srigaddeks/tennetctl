"""monitoring.dashboards.list — list dashboards visible to the caller."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

Node = _catalog_node.Node


class ListDashboards(Node):
    key = "monitoring.dashboards.list"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        user_id: str

    class Output(BaseModel):
        items: list[dict[str, Any]]
        total: int

    async def run(
        self, ctx: Any, inputs: "ListDashboards.Input",
    ) -> "ListDashboards.Output":
        conn = ctx.conn
        rows = await _service.list_dashboards(
            conn, org_id=inputs.org_id, owner_user_id=inputs.user_id,
        )
        return self.Output(items=rows, total=len(rows))
