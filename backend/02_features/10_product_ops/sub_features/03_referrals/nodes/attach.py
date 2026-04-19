"""
product_ops.referrals.attach — effect node, tx=own.

Called from the browser SDK landing handler when ?ref=<code> is present.
Emits audit (effect-must-emit-audit), writes the touch + referral_attached
event into the product_ops events stream.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.service"
)
_catalog: Any = import_module("backend.01_catalog")


class AttachReferral(_node_mod.Node):
    key = "product_ops.referrals.attach"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        code: str
        workspace_id: str
        anonymous_id: str
        landing_url: str | None = None

    class Output(BaseModel):
        visitor_id: str
        referral_code_id: str
        code: str
        referrer_user_id: str

    async def run(self, ctx: Any, inputs: Any) -> "AttachReferral.Output":
        body = _schemas.AttachReferralBody(**inputs.model_dump())
        pool = ctx.extras.get("pool")
        result = await _service.attach_referral(pool, ctx.conn, ctx, body=body)
        # Audit emission for the effect
        try:
            from dataclasses import replace as _replace
            scoped = _replace(ctx, audit_category="setup")
            await _catalog.run_node(
                pool, "audit.events.emit", scoped,
                {
                    "event_key": "product_ops.referrals.attached",
                    "outcome": "success",
                    "metadata": {
                        "code": inputs.code,
                        "workspace_id": inputs.workspace_id,
                        "visitor_id": result["visitor_id"],
                    },
                },
            )
        except Exception:
            pass
        return self.Output(**result)
