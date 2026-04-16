"""vault.configs.update — effect node. PATCH value / description / is_active."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)

_MARKER = "__omitted__"


class VaultConfigsUpdate(_node_mod.Node):
    key = "vault.configs.update"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str
        # Use a sentinel to distinguish "field omitted" from "explicit null".
        value: Any = Field(default=_MARKER)
        description: Any = Field(default=_MARKER)
        is_active: Any = Field(default=_MARKER)

    class Output(BaseModel):
        config: dict

    async def run(self, ctx: Any, inputs: Input) -> "VaultConfigsUpdate.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        if pool is None:
            raise RuntimeError("NodeContext.extras must carry 'pool' for vault.configs.update")

        has_value = inputs.value != _MARKER
        has_description = inputs.description != _MARKER
        has_is_active = inputs.is_active != _MARKER

        config = await _service.update_config(
            pool, ctx.conn, ctx,
            config_id=inputs.id,
            value=inputs.value if has_value else None,
            description=inputs.description if has_description else None,
            is_active=inputs.is_active if has_is_active else None,
            has_value=has_value,
            has_description=has_description,
            has_is_active=has_is_active,
        )
        return self.Output(config=config)
