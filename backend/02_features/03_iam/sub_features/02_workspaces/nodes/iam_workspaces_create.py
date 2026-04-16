"""
iam.workspaces.create — effect node.

Validates parent org exists, creates a workspace with per-org slug uniqueness,
emits audit iam.workspaces.created. All writes atomic on caller's transaction.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.service"
)


class WorkspacesCreate(_node_mod.Node):
    key = "iam.workspaces.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        org_id: str
        slug: str
        display_name: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        workspace: dict

    async def run(self, ctx: Any, inputs: Input) -> "WorkspacesCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError(
                "NodeContext.extras['pool'] required for iam.workspaces.create"
            )
        ws = await _service.create_workspace(
            pool,
            ctx.conn,
            ctx,
            org_id=inputs.org_id,
            slug=inputs.slug,
            display_name=inputs.display_name,
        )
        return self.Output(workspace=ws)
