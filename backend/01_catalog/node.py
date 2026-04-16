"""
Node base class — the contract every handler class must implement (NCP v1 §4).

Subclasses MUST override `key` and `kind`, define `Input` and `Output` as
Pydantic BaseModel subclasses, and implement `async def run(ctx, inputs)`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Node:
    """Base class for all node handlers."""

    key: str = ""          # e.g. "iam.orgs.create"
    kind: str = ""         # "request" | "effect" | "control"

    class Input(BaseModel):
        pass

    class Output(BaseModel):
        pass

    async def run(self, ctx: Any, inputs: Any) -> Any:
        """
        Execute the node. Override in subclasses.

        ctx: NodeContext — audit + tracing + (optional) db conn
        inputs: instance of self.Input (pre-validated by runner)
        returns: instance of self.Output OR dict matching self.Output shape
        """
        raise NotImplementedError(
            f"Node {type(self).__name__} ({self.key!r}) does not implement run()"
        )
