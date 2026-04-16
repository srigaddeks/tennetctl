"""featureflags.overrides.set — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.04_overrides.service"
)


class OverridesSet(_node_mod.Node):
    key = "featureflags.overrides.set"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        flag_id: str
        environment: str
        entity_type: str
        entity_id: str
        value: Any
        reason: str | None = None
        idempotency_key: str | None = None

    class Output(BaseModel):
        override: dict

    async def run(self, ctx: Any, inputs: Input) -> "OverridesSet.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        o = await _service.create_override(
            pool, ctx.conn, ctx,
            flag_id=inputs.flag_id,
            environment=inputs.environment,
            entity_type=inputs.entity_type,
            entity_id=inputs.entity_id,
            value=inputs.value,
            reason=inputs.reason,
        )
        return self.Output(override=o)
