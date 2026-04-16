"""vault.configs.create — effect node. Create a plaintext typed config value."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)


class VaultConfigsCreate(_node_mod.Node):
    key = "vault.configs.create"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        key: str
        value_type: Literal["boolean", "string", "number", "json"]
        value: Any
        description: str | None = Field(default=None, max_length=500)
        scope: Literal["global", "org", "workspace"] = "global"
        org_id: str | None = None
        workspace_id: str | None = None

        @model_validator(mode="after")
        def _scope_shape(self) -> "VaultConfigsCreate.Input":
            if self.scope == "global" and (self.org_id or self.workspace_id):
                raise ValueError("scope='global' requires org_id+workspace_id null")
            if self.scope == "org" and (not self.org_id or self.workspace_id):
                raise ValueError("scope='org' requires org_id set + workspace_id null")
            if self.scope == "workspace" and (not self.org_id or not self.workspace_id):
                raise ValueError("scope='workspace' requires both org_id + workspace_id")
            return self

    class Output(BaseModel):
        config: dict

    async def run(self, ctx: Any, inputs: Input) -> "VaultConfigsCreate.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        if pool is None:
            raise RuntimeError("NodeContext.extras must carry 'pool' for vault.configs.create")
        config = await _service.create_config(
            pool, ctx.conn, ctx,
            key=inputs.key,
            value_type=inputs.value_type,
            value=inputs.value,
            description=inputs.description,
            scope=inputs.scope,
            org_id=inputs.org_id,
            workspace_id=inputs.workspace_id,
        )
        return self.Output(config=config)
