"""Test fixture — control node that fails twice then succeeds.

Used by runner retry tests (AC-4). Class-level counter so the flakiness
is visible across runner retry attempts within one test; tests reset
`FlakyNode._calls = 0` in their fixture setup."""

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_node: Any = import_module("backend.01_catalog.node")
_errors: Any = import_module("backend.01_catalog.errors")


class FlakyNode(_node.Node):
    key = "core.sample.flaky"
    kind = "control"

    _calls: int = 0

    class Input(BaseModel):
        idempotency_key: str

    class Output(BaseModel):
        ok: bool = True
        attempts: int

    async def run(self, ctx, inputs):  # type: ignore[no-untyped-def]
        type(self)._calls += 1
        if type(self)._calls < 3:
            raise _errors.TransientError(
                f"flaky failure {type(self)._calls}", node_key=self.key,
            )
        return self.Output(attempts=type(self)._calls)
