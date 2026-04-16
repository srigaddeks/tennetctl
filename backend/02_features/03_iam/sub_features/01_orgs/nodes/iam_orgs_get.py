"""
iam.orgs.get — control node (read-only cross-sub-feature lookup).

Returns the flat v_orgs row or None. Kind is `control` with emits_audit=false:
NCP v1 §11 describes control as "flow logic only", widened here to include
read-only DB lookups so users/roles/workspaces can validate tenant scope without
emitting audit. Documented in Plan 04-01 SUMMARY; NCP doc-sync sits in v0.1.5.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.service"
)


class OrgsGet(_node_mod.Node):
    key = "iam.orgs.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        org: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "OrgsGet.Output":
        org = await _service.get_org(ctx.conn, ctx, org_id=inputs.id)
        return self.Output(org=org)
