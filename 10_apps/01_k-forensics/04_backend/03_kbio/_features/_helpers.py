"""Shared helper utilities for feature extractors.

Pure functions for safe type coercion of raw telemetry data.
No external dependencies.
"""
from __future__ import annotations

from typing import Any


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float, replacing None/-1 with default."""
    if val is None or val == -1:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_list(val: Any, expected_len: int, default: float = 0.0) -> list[float]:
    """Convert to list of floats with expected length.

    Pads with *default* if too short, truncates if too long.
    Non-list input returns a list of *default* values.
    """
    if not isinstance(val, (list, tuple)):
        return [default] * expected_len
    result = [_safe_float(v, default) for v in val]
    if len(result) < expected_len:
        result.extend([default] * (expected_len - len(result)))
    return result[:expected_len]
