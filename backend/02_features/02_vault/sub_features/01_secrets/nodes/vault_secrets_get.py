"""
vault.secrets.get — request node.

Returns the plaintext value of a vault key via the in-process VaultClient (SWR cache).
Does not emit audit — the node path is the hot path used by OAuth/session/argon2 reads;
HTTP GET /v1/vault/{key} is the audited admin path. See AC-5 of plan 07-01.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_client_mod: Any = import_module("backend.02_features.02_vault.client")


class VaultSecretsGet(_node_mod.Node):
    key = "vault.secrets.get"
    kind = "request"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        key: str

    class Output(BaseModel):
        value: str
        version: int

    async def run(self, ctx: Any, inputs: Input) -> "VaultSecretsGet.Output":
        extras = ctx.extras or {}
        vault = extras.get("vault")
        if vault is None:
            raise RuntimeError(
                "NodeContext.extras must carry 'vault' for vault.secrets.get"
            )
        try:
            value, version = await vault.get_with_version(inputs.key)
        except _client_mod.VaultSecretNotFound as e:
            raise RuntimeError(f"vault key {inputs.key!r} not found") from e
        return self.Output(value=value, version=version)
