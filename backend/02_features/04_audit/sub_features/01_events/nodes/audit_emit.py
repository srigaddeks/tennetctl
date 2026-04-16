"""
audit.emit — the canonical audit emitter.

Every effect node in the platform calls `run_node("audit.emit", ctx, {...})`
after its mutation lands. This handler writes a row into "04_audit"."60_evt_audit"
using NodeContext for scope + trace propagation and caller-supplied inputs for
event_key, outcome, metadata.

Scope enforcement: the DB CHECK constraint chk_evt_audit_scope rejects any row
where audit_category is not setup AND outcome is not failure AND any of
(actor_user_id, actor_session_id, org_id, workspace_id) is NULL. No code path
can bypass this.

Transaction mode: caller — runner passes the caller's conn, so the audit row
commits or rolls back with the caller's transaction (atomic audit).
"""

from __future__ import annotations

import re
from importlib import import_module
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

_node_mod: Any = import_module("backend.01_catalog.node")
_core_id: Any = import_module("backend.01_core.id")


_EVENT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")


class EmitAudit(_node_mod.Node):
    key = "audit.events.emit"
    kind = "effect"

    class Input(BaseModel):
        event_key: str
        outcome: Literal["success", "failure"] = "success"
        metadata: dict[str, Any] = Field(default_factory=dict)

        @field_validator("event_key")
        @classmethod
        def _event_key_shape(cls, v: str) -> str:
            if not _EVENT_KEY_RE.match(v):
                raise ValueError(
                    f"event_key {v!r} must match '<feature>.<sub>.<action>' (dotted snake_case)"
                )
            return v

    class Output(BaseModel):
        audit_id: str

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        audit_id = _core_id.uuid7()
        await ctx.conn.execute(
            """
            INSERT INTO "04_audit"."60_evt_audit"
              (id, event_key,
               actor_user_id, actor_session_id, org_id, workspace_id,
               trace_id, span_id, parent_span_id,
               audit_category, outcome, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            audit_id, inputs.event_key,
            ctx.user_id, ctx.session_id, ctx.org_id, ctx.workspace_id,
            ctx.trace_id, ctx.span_id, ctx.parent_span_id,
            ctx.audit_category, inputs.outcome, inputs.metadata,
        )
        return self.Output(audit_id=audit_id)
