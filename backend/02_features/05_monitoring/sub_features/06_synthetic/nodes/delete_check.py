"""monitoring.synthetic.delete — soft-delete a synthetic check."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.service"
)

Node = _catalog_node.Node


class DeleteSyntheticCheck(Node):
    key = "monitoring.synthetic.delete"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        id: str

    class Output(BaseModel):
        ok: bool

    async def run(
        self, ctx: Any, inputs: "DeleteSyntheticCheck.Input",
    ) -> "DeleteSyntheticCheck.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        ok = await _service.delete(conn, ctx, pool, org_id=inputs.org_id, id=inputs.id)
        return self.Output(ok=ok)
