"""vault.configs.get — control node. Read-only lookup for cross-sub-feature callers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)


class VaultConfigsGet(_node_mod.Node):
    key = "vault.configs.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        config: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "VaultConfigsGet.Output":
        config = await _service.get_config(ctx.conn, ctx, config_id=inputs.id)
        if config is not None and config.get("deleted_at") is not None:
            config = None
        return self.Output(config=config)
