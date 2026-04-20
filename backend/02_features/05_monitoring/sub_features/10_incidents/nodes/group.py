"""monitoring.incidents.group — group alert into incident node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class GroupAlert(Node):
    key = "monitoring.incidents.group"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        alert_event_id: str
        rule_id: str
        org_id: str
        fingerprint: str
        labels: dict = {}
        severity_id: int = 0
        rule_name: str = ""

    class Output(BaseModel):
        incident_id: str
        is_new: bool
        alert_count: int

    async def run(self, ctx: Any, inputs: "GroupAlert.Input") -> "GroupAlert.Output":
        """Group alert event into incident. Placeholder implementation.

        Uses advisory lock to prevent race conditions. Creates new incident
        or joins alert to existing incident based on grouping strategy.
        """
        return self.Output(
            incident_id=inputs.alert_event_id,
            is_new=True,
            alert_count=1,
        )
