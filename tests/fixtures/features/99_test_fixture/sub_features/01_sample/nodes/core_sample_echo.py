"""Test fixture — control node that echoes input with a derived field.

Used by runner tests (AC-2 happy path, AC-1 ctx propagation)."""

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_node: Any = import_module("backend.01_catalog.node")


class EchoNode(_node.Node):
    key = "core.sample.echo"
    kind = "control"

    class Input(BaseModel):
        msg: str

    class Output(BaseModel):
        msg: str
        echoed: bool = True
        trace_id: str = ""
        parent_span_id: str | None = None

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        return self.Output(
            msg=inputs.msg,
            trace_id=ctx.trace_id,
            parent_span_id=ctx.parent_span_id,
        )
