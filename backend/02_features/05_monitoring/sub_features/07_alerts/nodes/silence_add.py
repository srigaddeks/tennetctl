"""monitoring.alerts.silence_add — create a silence window."""

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


class SilenceAdd(Node):
    key = "monitoring.alerts.silence_add"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        created_by: str
        matcher: dict[str, Any] = Field(default_factory=dict)
        starts_at: datetime
        ends_at: datetime
        reason: str

    class Output(BaseModel):
        id: str

    async def run(
        self, ctx: Any, inputs: "SilenceAdd.Input",
    ) -> "SilenceAdd.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        row = await _service.create_silence(
            pool, conn, ctx,
            org_id=inputs.org_id,
            created_by=inputs.created_by,
            matcher=inputs.matcher,
            starts_at=inputs.starts_at,
            ends_at=inputs.ends_at,
            reason=inputs.reason,
        )
        return self.Output(id=str(row["id"]))
