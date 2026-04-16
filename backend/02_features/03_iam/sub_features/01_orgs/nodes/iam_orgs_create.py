"""
iam.orgs.create — effect node.

Creates an org (fct_orgs row + display_name attr) and emits audit iam.orgs.created.
Runs on the caller's transaction (tx=caller) so all three writes (fct + dtl + audit)
commit or roll back atomically.

Cross-sub-feature callers reach us via `run_node("iam.orgs.create", ctx, {...})`.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.service"
)


class OrgsCreate(_node_mod.Node):
    key = "iam.orgs.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        slug: str
        display_name: str
        # Reserved for future idempotency support; runner's v1 cache is deferred.
        idempotency_key: str | None = None

    class Output(BaseModel):
        org: dict

    async def run(self, ctx: Any, inputs: Input) -> "OrgsCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError(
                "NodeContext.extras['pool'] required for iam.orgs.create "
                "(audit emission needs pool for runner lookup)."
            )
        org = await _service.create_org(
            pool,
            ctx.conn,
            ctx,
            slug=inputs.slug,
            display_name=inputs.display_name,
        )
        return self.Output(org=org)
