"""iam.groups.get — control node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.service"
)


class GroupsGet(_node_mod.Node):
    key = "iam.groups.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        group: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "GroupsGet.Output":
        g = await _service.get_group(ctx.conn, ctx, group_id=inputs.id)
        return self.Output(group=g)
