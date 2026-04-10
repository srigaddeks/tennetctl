"""Signal system type definitions.

Shared TypedDicts for signal definitions, results, and configuration.
"""
from __future__ import annotations

from typing import Any, Callable, TypedDict


class SignalResult(TypedDict):
    """Output of a single signal function."""

    value: bool | float
    confidence: float
    details: dict[str, Any]


class SignalDef(TypedDict):
    """Internal registry entry for a signal."""

    code: str
    name: str
    description: str
    category: str
    signal_type: str  # "boolean" | "score"
    default_config: dict[str, Any]
    severity: int  # 0-100
    tags: list[str]
    function: Callable[[dict[str, Any], dict[str, Any]], SignalResult]
