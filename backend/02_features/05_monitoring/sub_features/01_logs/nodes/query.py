"""monitoring.logs.query — DSL query node. Request-kind, read-only."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.service"
)

Node = _catalog_node.Node


class LogsQueryNode(Node):
    key = "monitoring.logs.query"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        dsl: dict[str, Any]

    class Output(BaseModel):
        items: list[dict[str, Any]]
        next_cursor: str | None = None

    async def run(
        self, ctx: Any, inputs: "LogsQueryNode.Input"
    ) -> "LogsQueryNode.Output":
        conn = ctx.conn
        items, next_cursor = await _service.query(conn, ctx, inputs.dsl)
        return self.Output(items=items, next_cursor=next_cursor)
