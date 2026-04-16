"""iam.memberships.workspace.assign — effect node. org_id auto-derived from workspace."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.service"
)


class MembershipsWorkspaceAssign(_node_mod.Node):
    key = "iam.memberships.workspace.assign"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        user_id: str
        workspace_id: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        membership: dict

    async def run(self, ctx: Any, inputs: Input) -> "MembershipsWorkspaceAssign.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        m = await _service.assign_workspace(
            pool, ctx.conn, ctx,
            user_id=inputs.user_id,
            workspace_id=inputs.workspace_id,
        )
        return self.Output(membership=m)
