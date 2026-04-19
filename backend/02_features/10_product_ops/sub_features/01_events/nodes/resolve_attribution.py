"""
product_ops.events.attribution_resolve — read-only control node.

Returns {visitor_id, first_touch, last_touch}. Used by Phase 48's generalized
funnel/cohort engine to attribute conversions back to acquisition source.

tx=caller (Phase 10 Plan 01 decision) — caller passes ctx.conn for read.
"""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.service"
)


class _Touch(BaseModel):
    occurred_at: datetime | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    utm_term: str | None
    utm_content: str | None
    referrer: str | None
    landing_url: str | None


class ResolveAttribution(_node_mod.Node):
    key = "product_ops.events.attribution_resolve"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        visitor_id: str

    class Output(BaseModel):
        visitor_id: str
        first_touch: _Touch | None
        last_touch: _Touch | None

    async def run(self, ctx: Any, inputs: Any) -> "ResolveAttribution.Output":
        result = await _service.resolve_attribution(
            ctx.conn, visitor_id=inputs.visitor_id,
        )
        return self.Output(**result)
