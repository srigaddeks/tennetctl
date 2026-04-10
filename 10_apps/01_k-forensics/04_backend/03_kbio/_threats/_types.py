"""Threat type system type definitions."""
from __future__ import annotations

from typing import Any, TypedDict


class ThreatTypeDef(TypedDict):
    """Internal registry entry for a threat type."""

    code: str
    name: str
    description: str
    category: str
    severity: int  # 0-100
    default_action: str  # allow | monitor | challenge | block | flag | throttle
    conditions: dict[str, Any]  # JSON rule engine format
    default_config: dict[str, Any]
    reason_template: str
    tags: list[str]


class ThreatResult(TypedDict):
    """Output when a threat type matches."""

    code: str
    name: str
    category: str
    severity: int
    default_action: str
    reason: str
    matched_signals: list[str]
    execution_ms: float
