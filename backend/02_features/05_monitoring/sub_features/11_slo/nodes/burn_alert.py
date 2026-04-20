"""monitoring.slo.burn_alert — emit SLO burn rate alert node."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any, Literal
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node

logger = logging.getLogger("tennetctl.monitoring.slo.burn_alert")


class EmitBurnAlert(Node):
    key = "monitoring.slo.burn_alert"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        slo_id: str
        org_id: str
        breach_kind: Literal["fast_burn", "slow_burn"]
        burn_rate: float
        severity_id: int

    class Output(BaseModel):
        alert_event_id: str

    async def run(self, ctx: Any, inputs: "EmitBurnAlert.Input") -> "EmitBurnAlert.Output":
        """Emit a synthetic alert event for SLO burn rate breach. Placeholder implementation.

        Creates an evt_monitoring_alert_events row with virtual rule key "slo:{slo_id}".
        Reuses alert → incident → escalation → action chain for SLO breaches.
        """
        return self.Output(alert_event_id=inputs.slo_id)
