"""
iam.auth.validate_session — request node.

Stateless validation hook used by the auth middleware: decode + verify the
opaque token, fetch the row, return scope. Returns session=None when invalid
(signature mismatch, expired, revoked, deleted) — caller decides whether to
401 or pass through.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_sessions: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)


class AuthValidateSession(_node_mod.Node):
    key = "iam.auth.validate_session"
    kind = "request"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        token: str

    class Output(BaseModel):
        session: dict | None

    async def run(
        self, ctx: Any, inputs: "AuthValidateSession.Input",
    ) -> "AuthValidateSession.Output":
        vault = ctx.extras.get("vault") if ctx.extras else None
        if vault is None:
            raise RuntimeError(
                "NodeContext.extras['vault'] required for iam.auth.validate_session"
            )
        row = await _sessions.validate_token(
            ctx.conn, vault_client=vault, token=inputs.token,
        )
        return self.Output(session=row)
