"""monitoring.synthetic.create — create a synthetic check."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, Field

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.service"
)

Node = _catalog_node.Node


class CreateSyntheticCheck(Node):
    key = "monitoring.synthetic.create"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        name: str
        target_url: str
        method: str = "GET"
        expected_status: int = 200
        timeout_ms: int = 5000
        interval_seconds: int = 60
        headers: dict[str, Any] = Field(default_factory=dict)
        body: str | None = None
        assertions: list[dict[str, Any]] = Field(default_factory=list)

    class Output(BaseModel):
        id: str

    async def run(
        self, ctx: Any, inputs: "CreateSyntheticCheck.Input",
    ) -> "CreateSyntheticCheck.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        row = await _service.create(
            conn, ctx, pool,
            org_id=inputs.org_id, name=inputs.name, target_url=inputs.target_url,
            method=inputs.method, expected_status=inputs.expected_status,
            timeout_ms=inputs.timeout_ms, interval_seconds=inputs.interval_seconds,
            headers=inputs.headers, body=inputs.body, assertions=inputs.assertions,
        )
        return self.Output(id=str(row["id"]))
