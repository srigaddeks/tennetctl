"""featureflags.flags.create — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.01_flags.service"
)


class FlagsCreate(_node_mod.Node):
    key = "featureflags.flags.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        scope: str
        org_id: str | None = None
        application_id: str | None = None
        flag_key: str
        value_type: str
        default_value: Any
        description: str | None = None
        idempotency_key: str | None = None

    class Output(BaseModel):
        flag: dict

    async def run(self, ctx: Any, inputs: Input) -> "FlagsCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        flag = await _service.create_flag(
            pool, ctx.conn, ctx,
            scope=inputs.scope,
            org_id=inputs.org_id,
            application_id=inputs.application_id,
            flag_key=inputs.flag_key,
            value_type=inputs.value_type,
            default_value=inputs.default_value,
            description=inputs.description,
        )
        return self.Output(flag=flag)
