"""monitoring.metrics.set_gauge — record a gauge observation.

Effect node, tx=caller. Hot-path — skips audit on success per the 13-01
ingest-path carve-out. Emits a failure audit on cardinality reject.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, Field

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)
_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.schemas"
)

Node = _catalog_node.Node


class SetGauge(Node):
    key = "monitoring.metrics.set_gauge"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        metric_key: str
        labels: dict[str, str] = Field(default_factory=dict)
        value: float
        resource: dict[str, Any] | None = None

    class Output(BaseModel):
        metric_id: int
        accepted: bool

    async def run(self, ctx: Any, inputs: "SetGauge.Input") -> "SetGauge.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        req = _schemas.MetricSetRequest(
            labels=dict(inputs.labels),
            value=float(inputs.value),
            resource=inputs.resource,
        )
        result = await _service.set_gauge(
            conn, pool, ctx, org_id=inputs.org_id, key=inputs.metric_key, req=req,
        )
        return self.Output(
            metric_id=int(result["metric_id"]),
            accepted=bool(result["accepted"]),
        )
