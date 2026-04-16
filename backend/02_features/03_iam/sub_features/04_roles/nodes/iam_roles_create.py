"""iam.roles.create — effect node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.service"
)


class RolesCreate(_node_mod.Node):
    key = "iam.roles.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        org_id: str | None = None
        role_type: str
        code: str
        label: str
        description: str | None = None
        idempotency_key: str | None = None

    class Output(BaseModel):
        role: dict

    async def run(self, ctx: Any, inputs: Input) -> "RolesCreate.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError("NodeContext.extras['pool'] required")
        role = await _service.create_role(
            pool, ctx.conn, ctx,
            org_id=inputs.org_id,
            role_type=inputs.role_type,
            code=inputs.code,
            label=inputs.label,
            description=inputs.description,
        )
        return self.Output(role=role)
