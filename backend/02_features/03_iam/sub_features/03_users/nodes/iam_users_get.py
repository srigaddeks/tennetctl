"""
iam.users.get — control node (read-only cross-sub-feature lookup).

Phase 6 roles/groups will call this to validate user existence before assignment.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)


class UsersGet(_node_mod.Node):
    key = "iam.users.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        user: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "UsersGet.Output":
        user = await _service.get_user(ctx.conn, ctx, user_id=inputs.id)
        return self.Output(user=user)
