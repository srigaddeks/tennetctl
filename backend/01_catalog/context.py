"""
NodeContext — carried through every `run_node` call (NCP v1 §6).

Immutable (frozen dataclass). Every run_node call derives a child context
with a fresh span_id so traces form a tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")


@dataclass(frozen=True)
class NodeContext:
    # Identity (audit scope)
    user_id: str | None = None
    session_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None

    # Tracing
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str | None = None

    # Runtime
    conn: Any = None  # asyncpg.Connection | None; typed as Any to avoid hard import
    request_id: str = ""

    # Policy
    audit_category: str = "system"  # system | user | integration | setup
    dry_run: bool = False
    timeout_override_ms: int | None = None

    # Free-form extras (rarely used; kept for future need — NCP §6 extras)
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def system(cls) -> "NodeContext":
        """Factory for system-originated calls (no user, trace fresh)."""
        return cls(
            audit_category="system",
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(),
        )

    def child_span(self, _node_key: str) -> "NodeContext":
        """
        Derive a child context for the next hop. Fresh span_id, parent links to us.
        trace_id propagates (or generates if root context was empty).
        """
        new_trace_id = self.trace_id or _core_id.uuid7()
        return replace(
            self,
            trace_id=new_trace_id,
            span_id=_core_id.uuid7(),
            parent_span_id=self.span_id or None,
        )
