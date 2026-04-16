"""Test fixture — control node that sleeps 2s (used to verify runner timeout)."""

import asyncio
from importlib import import_module
from typing import Any

from pydantic import BaseModel

_node: Any = import_module("backend.01_catalog.node")


class SlowNode(_node.Node):
    key = "core.sample.slow"
    kind = "control"

    class Input(BaseModel):
        pass

    class Output(BaseModel):
        slept: bool = True

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        await asyncio.sleep(2.0)
        return self.Output()
