"""iam.memberships.workspace.revoke — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.service"
)


class MembershipsWorkspaceRevoke(_node_mod.Node):
    key = "iam.memberships.workspace.revoke"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        membership_id: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        membership_id: str

    async def run(self, ctx: Any, inputs: Input) -> "MembershipsWorkspaceRevoke.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        await _service.revoke_workspace(
            pool, ctx.conn, ctx, membership_id=inputs.membership_id,
        )
        return self.Output(membership_id=inputs.membership_id)
