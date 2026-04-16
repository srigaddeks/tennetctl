"""
vault.secrets.delete — effect node.

Soft-deletes every version of a key. Emits audit vault.secrets.deleted. Invalidates
the in-process cache.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)


class VaultSecretsDelete(_node_mod.Node):
    key = "vault.secrets.delete"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        key: str

    class Output(BaseModel):
        key: str

    async def run(self, ctx: Any, inputs: Input) -> "VaultSecretsDelete.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        vault = extras.get("vault")
        if pool is None or vault is None:
            raise RuntimeError(
                "NodeContext.extras must carry 'pool' and 'vault' for vault.secrets.delete"
            )
        await _service.delete_secret(
            pool, ctx.conn, ctx, vault_client=vault, key=inputs.key,
        )
        return self.Output(key=inputs.key)
