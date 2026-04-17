"""
iam.auth.signin — effect node.

Wraps the signin service: verify credential + mint session + emit audit.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.service"
)


class AuthSignin(_node_mod.Node):
    key = "iam.auth.signin"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        email: str
        password: str = Field(min_length=1, max_length=512)
        idempotency_key: str | None = None

    class Output(BaseModel):
        token: str
        user: dict
        session: dict

    async def run(self, ctx: Any, inputs: "AuthSignin.Input") -> "AuthSignin.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        vault = ctx.extras.get("vault") if ctx.extras else None
        if pool is None or vault is None:
            raise RuntimeError(
                "NodeContext.extras['pool'] + ['vault'] required for iam.auth.signin"
            )
        token, user, session = await _service.signin(
            pool, ctx.conn, ctx,
            vault_client=vault,
            email=inputs.email,
            password=inputs.password,
        )
        return self.Output(token=token, user=user, session=dict(session))
