"""featureflags.rules.create — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.03_rules.service"
)


class RulesCreate(_node_mod.Node):
    key = "featureflags.rules.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        flag_id: str
        environment: str
        priority: int = Field(ge=0, le=32000)
        conditions: dict[str, Any]
        value: Any
        rollout_percentage: int = Field(default=100, ge=0, le=100)
        idempotency_key: str | None = None

    class Output(BaseModel):
        rule: dict

    async def run(self, ctx: Any, inputs: Input) -> "RulesCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        rule = await _service.create_rule(
            pool, ctx.conn, ctx,
            flag_id=inputs.flag_id,
            environment=inputs.environment,
            priority=inputs.priority,
            conditions=inputs.conditions,
            value=inputs.value,
            rollout_percentage=inputs.rollout_percentage,
        )
        return self.Output(rule=rule)
