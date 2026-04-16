"""
In-memory node registry — stores NodeContract instances by key.

Nodes are the platform-level building blocks. Each has a typed contract:
key, kind, config/input/output schemas, handler path.

Registry is in-memory only for now — no DB persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

_VALID_KINDS = frozenset({"request", "effect", "control"})


@dataclass(frozen=True)
class NodeContract:
    """Typed contract for a node in the workflow system."""

    key: str  # Namespaced, e.g. "iam.auth_required"
    kind: Literal["request", "effect", "control"]
    config_schema: dict  # JSON Schema for node configuration
    input_schema: dict  # JSON Schema for input
    output_schema: dict  # JSON Schema for output
    handler: str  # Dotted import path, e.g. "backend.02_features.iam.nodes.AuthRequired"


_registry: dict[str, NodeContract] = {}


def register(contract: NodeContract) -> None:
    """Register a node contract. Validates key format and kind."""
    if "." not in contract.key:
        raise ValueError(
            f"Node key must be namespaced (contain '.'): got '{contract.key}'"
        )
    if contract.kind not in _VALID_KINDS:
        raise ValueError(
            f"Node kind must be one of {_VALID_KINDS}: got '{contract.kind}'"
        )
    if contract.key in _registry:
        raise ValueError(f"Node already registered: '{contract.key}'")

    _registry[contract.key] = contract


def get(key: str) -> NodeContract | None:
    """Look up a node contract by key. Returns None if not found."""
    return _registry.get(key)


def list_all() -> list[NodeContract]:
    """Return all registered node contracts."""
    return list(_registry.values())


def clear() -> None:
    """Clear the registry. For testing only."""
    _registry.clear()
