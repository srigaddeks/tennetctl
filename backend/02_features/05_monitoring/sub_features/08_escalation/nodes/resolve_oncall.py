"""Node: monitoring.oncall.resolve — control node for on-call resolution."""

from __future__ import annotations

from typing import Any
from datetime import datetime

NODE_KEY = "monitoring.oncall.resolve"
NODE_KIND = "control"
NODE_TX_MODE = "none"
NODE_DESCRIPTION = "Resolve who is on-call for a schedule at a given time."

CONFIG_SCHEMA = {}
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "schedule_id": {"type": "string", "description": "On-call schedule ID"},
        "at_timestamp": {"type": "string", "description": "Timestamp to resolve for (ISO 8601)"},
    },
    "required": ["schedule_id"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "description": "User ID currently on-call"},
        "on_until": {"type": "string", "description": "Timestamp of next handover (ISO 8601)"},
    },
}


async def handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Resolve current on-call user. Placeholder for Phase 40 implementation."""
    # Placeholder: would call oncall module to resolve
    return {
        "user_id": None,
        "on_until": None,
    }


__all__ = [
    "NODE_KEY",
    "NODE_KIND",
    "NODE_TX_MODE",
    "CONFIG_SCHEMA",
    "INPUT_SCHEMA",
    "OUTPUT_SCHEMA",
    "handler",
]
