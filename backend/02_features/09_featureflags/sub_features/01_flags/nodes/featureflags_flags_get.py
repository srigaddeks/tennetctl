"""featureflags.flags.get — control node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.01_flags.service"
)


class FlagsGet(_node_mod.Node):
    key = "featureflags.flags.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        flag: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "FlagsGet.Output":
        flag = await _service.get_flag(ctx.conn, ctx, flag_id=inputs.id)
        return self.Output(flag=flag)
