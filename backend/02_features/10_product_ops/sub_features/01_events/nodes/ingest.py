"""
product_ops.events.ingest — the ingest node (kind=effect, tx=own).

Wraps service.ingest_batch with the Node contract. tx=own means the runner
opens a fresh asyncpg connection in its own transaction; conn lives on
ctx.conn for the duration of run().

Per ADR-030 + the manifest, this node DOES emit_audit (the per-batch
summary inside service.ingest_batch). Per-event audit is intentionally
bypassed — would amplify writes 100-1000x at SDK ingest scale.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.service"
)


class IngestProductEvents(_node_mod.Node):
    key = "product_ops.events.ingest"
    kind = "effect"

    class Input(BaseModel):
        """
        Mirrors TrackBatchIn but with the optional client_ip carried as a
        first-class input so callers (route → node) propagate it explicitly.
        """
        model_config = ConfigDict(extra="forbid")

        project_key: str = Field(min_length=1, max_length=256)
        events: list[dict] = Field(min_length=1, max_length=1000)
        dnt: bool = False
        client_ip: str | None = None

    class Output(BaseModel):
        accepted: int
        dropped_dnt: int
        dropped_capped: int

    async def run(self, ctx: Any, inputs: Any) -> "IngestProductEvents.Output":
        # Re-validate event shapes here so the route can pass dicts and the
        # node enforces the same TrackBatchIn schema regardless of caller.
        events = [_schemas.IngestEventIn(**e) for e in inputs.events]
        batch = _schemas.TrackBatchIn(
            project_key=inputs.project_key,
            events=events,
            dnt=inputs.dnt,
        )
        # Pool comes from ctx.extras (Plan 04-01 convention).
        pool = ctx.extras.get("pool")
        result = await _service.ingest_batch(
            pool, ctx.conn, ctx, batch, client_ip=inputs.client_ip,
        )
        return self.Output(**result)
