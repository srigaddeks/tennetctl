"""
iam.workspaces.get — control node (read-only cross-sub-feature lookup).

Returns flat v_workspaces row or None. No audit emission (kind=control).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.service"
)


class WorkspacesGet(_node_mod.Node):
    key = "iam.workspaces.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        workspace: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "WorkspacesGet.Output":
        ws = await _service.get_workspace(ctx.conn, ctx, workspace_id=inputs.id)
        return self.Output(workspace=ws)
