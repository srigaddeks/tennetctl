"""monitoring.actions.template_update — update action template node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class TemplateUpdate(Node):
    key = "monitoring.actions.template_update"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        template_id: str
        name: str | None = None
        body: str | None = None

    class Output(BaseModel):
        template_id: str

    async def run(self, ctx: Any, inputs: "TemplateUpdate.Input") -> "TemplateUpdate.Output":
        """Update action template. Placeholder implementation."""
        return self.Output(template_id=inputs.template_id)
