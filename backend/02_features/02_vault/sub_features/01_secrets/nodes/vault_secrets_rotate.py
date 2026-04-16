"""vault.secrets.rotate — effect node. Create version+1 under a fresh DEK."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)


class VaultSecretsRotate(_node_mod.Node):
    key = "vault.secrets.rotate"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        key: str
        value: str = Field(min_length=1, max_length=65536)
        description: str | None = None
        scope: Literal["global", "org", "workspace"] = "global"
        org_id: str | None = None
        workspace_id: str | None = None

        @model_validator(mode="after")
        def _scope_shape(self) -> "VaultSecretsRotate.Input":
            if self.scope == "global" and (self.org_id or self.workspace_id):
                raise ValueError("scope='global' requires org_id+workspace_id null")
            if self.scope == "org" and (not self.org_id or self.workspace_id):
                raise ValueError("scope='org' requires org_id set + workspace_id null")
            if self.scope == "workspace" and (not self.org_id or not self.workspace_id):
                raise ValueError("scope='workspace' requires both org_id + workspace_id")
            return self

    class Output(BaseModel):
        secret: dict

    async def run(self, ctx: Any, inputs: Input) -> "VaultSecretsRotate.Output":
        extras = ctx.extras or {}
        pool = extras.get("pool")
        vault = extras.get("vault")
        if pool is None or vault is None:
            raise RuntimeError(
                "NodeContext.extras must carry 'pool' and 'vault' for vault.secrets.rotate"
            )
        secret = await _service.rotate_secret(
            pool, ctx.conn, ctx,
            vault_client=vault,
            key=inputs.key,
            value=inputs.value,
            description=inputs.description,
            scope=inputs.scope,
            org_id=inputs.org_id,
            workspace_id=inputs.workspace_id,
        )
        return self.Output(secret=secret)
