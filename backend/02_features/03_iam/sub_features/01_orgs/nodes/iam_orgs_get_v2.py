"""
iam.orgs.get_v2 — control node (v2 of iam.orgs.get, Plan 39-03).

Returns {org, workspace_count}. This is the first real v1→v2 migration in the
codebase, executed to exercise NCP v1 §13's "paired-keys with deprecated_at +
replaced_by" story end-to-end. See ADR-032 for the recipe.

Breaking change vs v1: Output gains a required `workspace_count: int` field.
Callers that still want the flat shape keep using `iam.orgs.get` (deprecated
but alive); callers that want the count migrate to `iam.orgs.get_v2`.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.service"
)


class OrgsGetV2(_node_mod.Node):
    key = "iam.orgs.get_v2"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        org: dict | None
        workspace_count: int

    async def run(self, ctx: Any, inputs: "OrgsGetV2.Input") -> "OrgsGetV2.Output":
        org = await _service.get_org(ctx.conn, ctx, org_id=inputs.id)
        if org is None:
            return self.Output(org=None, workspace_count=0)
        # tx=caller: reuse caller's conn. View already filters deleted workspaces.
        count = await ctx.conn.fetchval(
            'SELECT COUNT(*) FROM "03_iam"."v_workspaces" '
            'WHERE org_id = $1 AND deleted_at IS NULL',
            inputs.id,
        )
        return self.Output(org=org, workspace_count=int(count or 0))
