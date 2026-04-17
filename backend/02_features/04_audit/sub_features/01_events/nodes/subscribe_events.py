"""
audit.events.subscribe — control node.

Polling-based outbox consumer. Callers (Notify subscription worker, webhook
dispatcher, export jobs) call run_node("audit.events.subscribe", ctx, {...})
with their last-seen outbox cursor id. Returns new events and the updated cursor.

Design:
  - Reads 61_evt_audit_outbox JOIN v_audit_events.
  - Returns events in ascending outbox id order (natural consumer order).
  - tx=caller: reuses ctx.conn (caller manages the connection).
  - Does NOT emit audit (matches audit.events.query hot-path bypass).

LISTEN/NOTIFY usage:
  Consumers that want wake-up instead of polling should open a dedicated
  LISTEN connection on channel 'audit_events' and call this node on each
  notification. The node itself only handles the poll step; LISTEN wiring
  is the caller's responsibility.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_node_mod: Any = import_module("backend.01_catalog.node")
_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.repository"
)


class AuditEventsSubscribe(_node_mod.Node):
    key = "audit.events.subscribe"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        since_id: int = Field(default=0, ge=0, description="Last outbox id seen; 0 = start")
        limit: int = Field(default=50, ge=1, le=500)
        org_id: str | None = Field(default=None, description="Tenant filter; None = all tenants")

    class Output(BaseModel):
        events: list[dict]
        last_outbox_id: int

    async def run(self, ctx: Any, inputs: "AuditEventsSubscribe.Input") -> "AuditEventsSubscribe.Output":
        if ctx.conn is None:
            raise RuntimeError(
                "audit.events.subscribe requires ctx.conn (tx=caller). "
                "Ensure the caller passes a live connection in NodeContext."
            )
        rows = await _repo.poll_outbox(
            ctx.conn,
            since_id=inputs.since_id,
            limit=inputs.limit,
            org_id=inputs.org_id,
        )
        from datetime import datetime
        serialized: list[dict] = []
        for row in rows:
            r = dict(row)
            ca = r.get("created_at")
            if isinstance(ca, datetime):
                r["created_at"] = ca.isoformat()
            serialized.append(r)

        last_id = rows[-1]["outbox_id"] if rows else inputs.since_id
        return self.Output(events=serialized, last_outbox_id=last_id)
