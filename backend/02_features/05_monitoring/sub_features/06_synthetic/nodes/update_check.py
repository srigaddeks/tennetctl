"""monitoring.synthetic.update — update a synthetic check."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.service"
)

Node = _catalog_node.Node


class UpdateSyntheticCheck(Node):
    key = "monitoring.synthetic.update"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        id: str
        name: str | None = None
        target_url: str | None = None
        method: str | None = None
        expected_status: int | None = None
        timeout_ms: int | None = None
        interval_seconds: int | None = None
        headers: dict[str, Any] | None = None
        body: str | None = None
        assertions: list[dict[str, Any]] | None = None
        is_active: bool | None = None

    class Output(BaseModel):
        id: str
        ok: bool

    async def run(
        self, ctx: Any, inputs: "UpdateSyntheticCheck.Input",
    ) -> "UpdateSyntheticCheck.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool") if hasattr(ctx, "extras") else None
        row = await _service.update(
            conn, ctx, pool,
            org_id=inputs.org_id, id=inputs.id,
            name=inputs.name, target_url=inputs.target_url, method=inputs.method,
            expected_status=inputs.expected_status, timeout_ms=inputs.timeout_ms,
            interval_seconds=inputs.interval_seconds, headers=inputs.headers,
            body=inputs.body, assertions=inputs.assertions, is_active=inputs.is_active,
        )
        return self.Output(id=inputs.id, ok=row is not None)
