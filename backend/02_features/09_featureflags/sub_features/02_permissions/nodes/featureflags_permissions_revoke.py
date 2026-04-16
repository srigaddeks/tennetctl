"""featureflags.permissions.revoke — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.02_permissions.service"
)


class PermissionsRevoke(_node_mod.Node):
    key = "featureflags.permissions.revoke"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        grant_id: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        grant_id: str

    async def run(self, ctx: Any, inputs: Input) -> "PermissionsRevoke.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        await _service.revoke_permission(
            pool, ctx.conn, ctx, grant_id=inputs.grant_id,
        )
        return self.Output(grant_id=inputs.grant_id)
