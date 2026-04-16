"""
iam.users.create — effect node.

Creates a user (fct + 3 dtl attrs) and emits audit iam.users.created. tx=caller.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)


class UsersCreate(_node_mod.Node):
    key = "iam.users.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        account_type: str
        email: str
        display_name: str
        avatar_url: str | None = None
        idempotency_key: str | None = None

    class Output(BaseModel):
        user: dict

    async def run(self, ctx: Any, inputs: Input) -> "UsersCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError(
                "NodeContext.extras['pool'] required for iam.users.create"
            )
        user = await _service.create_user(
            pool,
            ctx.conn,
            ctx,
            account_type=inputs.account_type,
            email=inputs.email,
            display_name=inputs.display_name,
            avatar_url=inputs.avatar_url,
        )
        return self.Output(user=user)
