"""monitoring.actions.template_delete — delete action template node."""

from __future__ import annotations

from typing import Any
from importlib import import_module
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")

Node = _catalog_node.Node


class TemplateDelete(Node):
    key = "monitoring.actions.template_delete"
    kind = "effect"
    emits_audit = True

    class Input(BaseModel):
        template_id: str

    class Output(BaseModel):
        deleted: bool

    async def run(self, ctx: Any, inputs: "TemplateDelete.Input") -> "TemplateDelete.Output":
        """Delete action template. Placeholder implementation."""
        return self.Output(deleted=True)
