"""monitoring.alerts.evaluate — run a single rule's evaluator cycle.

Effect node exposing the evaluator to the catalog surface. Used by the worker
at start-up to boot the loop, and by operators to force-evaluate a specific
rule (e.g. after editing condition thresholds).

Returns the count of transitions emitted during this evaluation.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_evaluator: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.evaluator"
)
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.repository"
)

Node = _catalog_node.Node


class EvaluateRule(Node):
    key = "monitoring.alerts.evaluate"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        rule_id: str
        org_id: str

    class Output(BaseModel):
        transitions: int
        evaluated: bool

    async def run(
        self, ctx: Any, inputs: "EvaluateRule.Input",
    ) -> "EvaluateRule.Output":
        conn = ctx.conn
        rule = await _repo.get_rule(conn, rule_id=inputs.rule_id, org_id=inputs.org_id)
        if rule is None:
            return self.Output(transitions=0, evaluated=False)
        transitions = await _evaluator.evaluate_rule(conn, rule, ctx)
        # Note: caller (worker) is responsible for applying transitions via
        # service.insert_alert_event / update_alert_event. This node only runs
        # the evaluator — useful for dry-run testing via the catalog surface.
        return self.Output(transitions=len(transitions), evaluated=True)
