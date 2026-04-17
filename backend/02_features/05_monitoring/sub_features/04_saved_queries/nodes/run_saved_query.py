"""monitoring.saved_queries.run — load a saved DSL and execute it."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.service"
)

Node = _catalog_node.Node


class RunSavedQuery(Node):
    key = "monitoring.saved_queries.run"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        id: str

    class Output(BaseModel):
        target: str
        items: list[dict[str, Any]]
        next_cursor: str | None = None

    async def run(
        self, ctx: Any, inputs: "RunSavedQuery.Input"
    ) -> "RunSavedQuery.Output":
        conn = ctx.conn
        result = await _service.run(conn, ctx, id=inputs.id)
        return self.Output(
            target=result["target"],
            items=result["items"],
            next_cursor=result.get("next_cursor"),
        )
