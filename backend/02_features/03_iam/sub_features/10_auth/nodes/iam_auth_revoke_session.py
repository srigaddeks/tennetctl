"""
iam.auth.revoke_session — effect node.

Marks the session row revoked + emits audit. Idempotent: revoking an already-
revoked session returns revoked=False but does not error.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.service"
)


class AuthRevokeSession(_node_mod.Node):
    key = "iam.auth.revoke_session"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        session_id: str
        user_id: str
        idempotency_key: str | None = None

    class Output(BaseModel):
        revoked: bool

    async def run(
        self, ctx: Any, inputs: "AuthRevokeSession.Input",
    ) -> "AuthRevokeSession.Output":
        pool = ctx.extras.get("pool") if ctx.extras else None
        if pool is None:
            raise RuntimeError(
                "NodeContext.extras['pool'] required for iam.auth.revoke_session"
            )
        revoked = await _service.signout(
            pool, ctx.conn, ctx,
            session_id=inputs.session_id, user_id=inputs.user_id,
        )
        return self.Output(revoked=revoked)
