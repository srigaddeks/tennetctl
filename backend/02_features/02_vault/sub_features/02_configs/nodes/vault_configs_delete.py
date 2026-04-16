"""vault.configs.delete — effect node. Soft-delete by id."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)


class VaultConfigsDelete(_node_mod.Node):
    key = "vault.configs.delete"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        id: str

    async def run(self, ctx: Any, inputs: Input) -> "VaultConfigsDelete.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        if pool is None:
            raise RuntimeError("NodeContext.extras must carry 'pool' for vault.configs.delete")
        await _service.delete_config(pool, ctx.conn, ctx, config_id=inputs.id)
        return self.Output(id=inputs.id)
