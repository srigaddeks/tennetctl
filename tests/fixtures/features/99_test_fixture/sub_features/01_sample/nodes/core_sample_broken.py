"""Test fixture — control node that raises DomainError (non-retryable).

Used by AC-4 to verify DomainError is NOT retried even when retries>0."""

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_node: Any = import_module("backend.01_catalog.node")
_errors: Any = import_module("backend.01_catalog.errors")


class BrokenNode(_node.Node):
    key = "core.sample.broken"
    kind = "control"

    _calls: int = 0

    class Input(BaseModel):
        idempotency_key: str

    class Output(BaseModel):
        ok: bool = False

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        type(self)._calls += 1
        raise _errors.DomainError(
            f"broken on call {type(self)._calls}", node_key=self.key,
        )
