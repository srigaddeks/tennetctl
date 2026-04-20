"""monitoring.actions.template_create — create action template node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class TemplateCreate(Node):
    key = "monitoring.actions.template_create"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        name: str
        kind: str
        body: str
        org_id: str = ""

    class Output(BaseModel):
        template_id: str

    async def run(self, ctx: Any, inputs: "TemplateCreate.Input") -> "TemplateCreate.Output":
        """Create action template. Placeholder implementation."""
        template_id = inputs.name  # Stub
        return self.Output(template_id=template_id)
