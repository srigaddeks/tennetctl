"""monitoring.escalation.resolve_oncall — resolve on-call user node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class ResolveOncall(Node):
    key = "monitoring.escalation.resolve_oncall"
    kind = "control"
    emits_audit = False

    class Input(BaseModel):
        schedule_id: str
        at_timestamp: str | None = None

    class Output(BaseModel):
        user_id: str | None
        on_until: str | None

    async def run(self, ctx: Any, inputs: "ResolveOncall.Input") -> "ResolveOncall.Output":
        """Resolve current on-call user. Placeholder implementation."""
        return self.Output(user_id=None, on_until=None)
