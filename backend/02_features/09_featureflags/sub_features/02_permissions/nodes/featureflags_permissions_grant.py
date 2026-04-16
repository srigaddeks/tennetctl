"""featureflags.permissions.grant — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.02_permissions.service"
)


class PermissionsGrant(_node_mod.Node):
    key = "featureflags.permissions.grant"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        role_id: str
        flag_id: str
        permission: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        grant: dict

    async def run(self, ctx: Any, inputs: Input) -> "PermissionsGrant.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        grant = await _service.grant_permission(
            pool, ctx.conn, ctx,
            role_id=inputs.role_id,
            flag_id=inputs.flag_id,
            permission=inputs.permission,
        )
        return self.Output(grant=grant)
