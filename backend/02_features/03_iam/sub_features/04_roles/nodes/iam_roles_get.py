"""iam.roles.get — control node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.service"
)


class RolesGet(_node_mod.Node):
    key = "iam.roles.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        role: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "RolesGet.Output":
        role = await _service.get_role(ctx.conn, ctx, role_id=inputs.id)
        return self.Output(role=role)
