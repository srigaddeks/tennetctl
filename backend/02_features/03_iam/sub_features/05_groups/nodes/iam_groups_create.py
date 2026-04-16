"""iam.groups.create — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.service"
)


class GroupsCreate(_node_mod.Node):
    key = "iam.groups.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        org_id: str
        code: str
        label: str
        description: str | None = None
        idempotency_key: str | None = None

    class Output(BaseModel):
        group: dict

    async def run(self, ctx: Any, inputs: Input) -> "GroupsCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        g = await _service.create_group(
            pool, ctx.conn, ctx,
            org_id=inputs.org_id,
            code=inputs.code,
            label=inputs.label,
            description=inputs.description,
        )
        return self.Output(group=g)
