"""monitoring.metrics.register — upsert a metric into the registry.

Effect node, tx=caller. Emits `monitoring.metrics.registered` audit event.
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


class RegisterMetric(Node):
    key = "monitoring.metrics.register"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        org_id: str
        key: str
        metric_kind: str = Field(alias="kind")  # avoid clash with Node.kind
        label_keys: list[str] = Field(default_factory=list)
        description: str = ""
        unit: str = ""
        histogram_buckets: list[float] | None = None
        max_cardinality: int = 1000

        model_config = {"populate_by_name": True}

    class Output(BaseModel):
        metric_id: int
        metric_key: str

    async def run(
        self, ctx: Any, inputs: "RegisterMetric.Input"
    ) -> "RegisterMetric.Output":
        conn = ctx.conn
        pool = ctx.extras.get("pool")
        req = _schemas.MetricRegisterRequest(
            key=inputs.key,
            kind=inputs.metric_kind,  # type: ignore[arg-type]
            label_keys=list(inputs.label_keys),
            description=inputs.description,
            unit=inputs.unit,
            histogram_buckets=(
                list(inputs.histogram_buckets) if inputs.histogram_buckets else None
            ),
            max_cardinality=int(inputs.max_cardinality),
        )
        row = await _service.register_metric(
            conn, pool, ctx, org_id=inputs.org_id, req=req,
        )
        return self.Output(metric_id=int(row["id"]), metric_key=row["key"])
