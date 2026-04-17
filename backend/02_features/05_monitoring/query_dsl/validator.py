"""Monitoring Query DSL — defensive validator.

The Pydantic models in ``types.py`` already enforce shape + single-op per
filter + regex limiter + timerange cap. The validator adds:

- Filter tree depth cap (max 10).
- A ``validate_*_query(payload)`` entrypoint that normalises input to a
  typed model and raises ``InvalidQueryError`` on failure.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import ValidationError as _PyValidationError

_types: Any = import_module("backend.02_features.05_monitoring.query_dsl.types")

FILTER_DEPTH_MAX = 10


class InvalidQueryError(ValueError):
    """Raised when a DSL query fails validation."""


def _filter_depth(node: Any, current: int = 0) -> int:
    if node is None:
        return current
    depth = current + 1
    if depth > FILTER_DEPTH_MAX:
        raise InvalidQueryError(
            f"filter tree depth exceeds {FILTER_DEPTH_MAX}",
        )
    if node.and_:
        return max(_filter_depth(c, depth) for c in node.and_)
    if node.or_:
        return max(_filter_depth(c, depth) for c in node.or_)
    if node.not_:
        return _filter_depth(node.not_, depth)
    return depth


def _depth_check(filter_node: Any) -> None:
    if filter_node is not None:
        _filter_depth(filter_node, 0)


def validate_logs_query(payload: dict[str, Any]) -> Any:
    try:
        q = _types.LogsQuery.model_validate(payload)
    except _PyValidationError as e:
        raise InvalidQueryError(str(e)) from e
    _depth_check(q.filter)
    return q


def validate_metrics_query(payload: dict[str, Any]) -> Any:
    try:
        q = _types.MetricsQuery.model_validate(payload)
    except _PyValidationError as e:
        raise InvalidQueryError(str(e)) from e
    _depth_check(q.filter)
    return q


def validate_traces_query(payload: dict[str, Any]) -> Any:
    try:
        q = _types.TracesQuery.model_validate(payload)
    except _PyValidationError as e:
        raise InvalidQueryError(str(e)) from e
    _depth_check(q.filter)
    return q


__all__ = [
    "InvalidQueryError",
    "FILTER_DEPTH_MAX",
    "validate_logs_query",
    "validate_metrics_query",
    "validate_traces_query",
]
