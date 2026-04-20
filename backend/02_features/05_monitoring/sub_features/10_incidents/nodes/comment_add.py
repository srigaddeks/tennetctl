"""monitoring.incidents.comment_add — add incident comment node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class AddIncidentComment(Node):
    key = "monitoring.incidents.comment_add"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        incident_id: str
        user_id: str
        body: str

    class Output(BaseModel):
        event_id: str
        incident_id: str

    async def run(
        self, ctx: Any, inputs: "AddIncidentComment.Input"
    ) -> "AddIncidentComment.Output":
        """Add comment to incident timeline. Placeholder implementation."""
        return self.Output(
            event_id=inputs.incident_id,
            incident_id=inputs.incident_id,
        )
