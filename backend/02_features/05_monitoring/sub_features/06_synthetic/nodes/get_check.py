"""monitoring.synthetic.get — fetch a synthetic check by id."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.service"
)

Node = _catalog_node.Node


class GetSyntheticCheck(Node):
    key = "monitoring.synthetic.get"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        org_id: str
        id: str

    class Output(BaseModel):
        id: str | None
        found: bool

    async def run(
        self, ctx: Any, inputs: "GetSyntheticCheck.Input",
    ) -> "GetSyntheticCheck.Output":
        conn = ctx.conn
        row = await _service.get(conn, org_id=inputs.org_id, id=inputs.id)
        return self.Output(id=row["id"] if row else None, found=row is not None)
