"""featureflags.evaluations.resolve — control node (read-only)."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.05_evaluations.service"
)


class EvaluationsResolve(_node_mod.Node):
    key = "featureflags.evaluations.resolve"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        flag_key: str
        environment: str
        context: dict[str, Any] = {}

    class Output(BaseModel):
        value: Any
        reason: str
        flag_id: str | None = None
        flag_scope: str | None = None
        rule_id: str | None = None
        override_id: str | None = None

    async def run(self, ctx: Any, inputs: Input) -> "EvaluationsResolve.Output":
        if ctx.conn is None:
            # Control nodes are tx=caller; conn is required.
            raise RuntimeError("evaluations.resolve requires ctx.conn")
        result = await _service.evaluate(
            ctx.conn,
            flag_key=inputs.flag_key,
            environment=inputs.environment,
            context=inputs.context,
        )
        return self.Output(**result)
