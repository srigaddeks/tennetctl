"""
audit.events.query — control node.

Read-only cross-sub-feature lookup over the audit event store. Consumers
(e.g. Notify subscription workers, admin dashboards, exports) call
run_node("audit.events.query", ctx, {...}) to page through events matching
a filter without duplicating WHERE-clause logic.

Hot-path bypass: this node does NOT emit audit (matches the vault precedent
— HTTP reads emit audit, node reads don't). tx=caller — reuses ctx.conn.
"""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.repository"
)


class QueryAuditEvents(_node_mod.Node):
    key = "audit.events.query"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        event_key: str | None = None
        category_code: str | None = None
        outcome: str | None = None
        actor_user_id: str | None = None
        actor_session_id: str | None = None
        org_id: str | None = None
        workspace_id: str | None = None
        trace_id: str | None = None
        since: datetime | None = None
        until: datetime | None = None
        q: str | None = None
        cursor: str | None = None
        limit: int = Field(default=50, ge=1, le=1000)

    class Output(BaseModel):
        items: list[dict]
        next_cursor: str | None = None

    async def run(self, ctx: Any, inputs: "QueryAuditEvents.Input") -> "QueryAuditEvents.Output":
        if ctx.conn is None:
            raise RuntimeError(
                "audit.events.query requires ctx.conn (tx=caller). "
                "Ensure the caller passes a live connection in NodeContext."
            )
        filters = {
            "event_key":        inputs.event_key,
            "category_code":    inputs.category_code,
            "outcome":          inputs.outcome,
            "actor_user_id":    inputs.actor_user_id,
            "actor_session_id": inputs.actor_session_id,
            "org_id":           inputs.org_id,
            "workspace_id":     inputs.workspace_id,
            "trace_id":         inputs.trace_id,
            "since":            inputs.since,
            "until":            inputs.until,
            "q":                inputs.q,
        }
        items, next_cursor = await _repo.list_events(
            ctx.conn,
            filters=filters,
            cursor=inputs.cursor,
            limit=inputs.limit,
        )
        # created_at is a datetime coming from the view — ISO-serialize for JSON-safety.
        serialized: list[dict] = []
        for row in items:
            r = dict(row)
            ca = r.get("created_at")
            if isinstance(ca, datetime):
                r["created_at"] = ca.isoformat()
            serialized.append(r)
        return self.Output(items=serialized, next_cursor=next_cursor)
