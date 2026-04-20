"""monitoring.actions.dispatch — dispatch action node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class DispatchAction(Node):
    key = "monitoring.actions.dispatch"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        delivery_id: str
        template_id: str
        rendered_body: str
        rendered_headers: dict = {}
        signing_secret: str | None = None

    class Output(BaseModel):
        success: bool
        status_code: int | None = None
        error_message: str | None = None

    async def run(
        self, ctx: Any, inputs: "DispatchAction.Input"
    ) -> "DispatchAction.Output":
        """Dispatch an action and update delivery record. Placeholder implementation."""
        return self.Output(
            success=True,
            status_code=200,
            error_message=None,
        )
