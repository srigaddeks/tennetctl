"""Test fixture — control node, no-op."""

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_node: Any = import_module("backend.01_catalog.node")


class PingNode(_node.Node):
    key = "core.sample.ping"
    kind = "control"

    class Input(BaseModel):
        pass

    class Output(BaseModel):
        pong: bool = True

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        return self.Output()
