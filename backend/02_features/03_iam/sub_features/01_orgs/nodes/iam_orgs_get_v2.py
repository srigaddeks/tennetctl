"""
iam.orgs.get_v2 — first node version bump (v1→v2 migration pattern).

This is the worked example for ADR-032 (Node Versioning Pattern). v2 adds
workspace_count to the output — a breaking Output-schema change. v1 stays live
but marked deprecated; callers choose which version to invoke. Both coexist
until v1 callers fully migrate + v1 is archived (future phase).

See: 03_docs/00_main/08_decisions/032_v1_to_v2_versioning_pattern.md
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

    async def run(self, ctx: Any, inputs: Input) -> "OrgsGetV2.Output":
        org = await _service.get_org(ctx.conn, ctx, org_id=inputs.id)

        # Count non-deleted workspaces in this org
        workspace_count = 0
        if org:
            row = await ctx.conn.fetchrow(
                'SELECT COUNT(*) as cnt FROM "03_iam"."v_workspaces" WHERE org_id = $1 AND deleted_at IS NULL',
                inputs.id,
            )
            workspace_count = int(row["cnt"]) if row else 0

        return self.Output(org=org, workspace_count=workspace_count)
