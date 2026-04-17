"""monitoring.metrics.observe_histogram — record a histogram observation.

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


class ObserveHistogram(Node):
    key = "monitoring.metrics.observe_histogram"
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

    async def run(
        self, ctx: Any, inputs: "ObserveHistogram.Input"
    ) -> "ObserveHistogram.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        req = _schemas.MetricObserveRequest(
            labels=dict(inputs.labels),
            value=float(inputs.value),
            resource=inputs.resource,
        )
        result = await _service.observe_histogram(
            conn, pool, ctx, org_id=inputs.org_id, key=inputs.metric_key, req=req,
        )
        return self.Output(
            metric_id=int(result["metric_id"]),
            accepted=bool(result["accepted"]),
        )
