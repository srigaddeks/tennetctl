"""
vault.secrets.put — effect node.

Encrypts + stores a new secret at version=1. Emits audit vault.secrets.created
atomically with the fct + dtl writes (tx=caller).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)


class VaultSecretsPut(_node_mod.Node):
    key = "vault.secrets.put"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        key: str
        value: str = Field(min_length=1, max_length=65536)
        description: str | None = None

    class Output(BaseModel):
        secret: dict

    async def run(self, ctx: Any, inputs: Input) -> "VaultSecretsPut.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        vault = extras.get("vault")
        if pool is None or vault is None:
            raise RuntimeError(
                "NodeContext.extras must carry 'pool' and 'vault' for vault.secrets.put"
            )
        secret = await _service.create_secret(
            pool, ctx.conn, ctx,
            vault_client=vault,
            key=inputs.key,
            value=inputs.value,
            description=inputs.description,
            source="node",
        )
        return self.Output(secret=secret)
