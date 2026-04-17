"""Monitoring Query DSL — public exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_types: Any = import_module("backend.02_features.05_monitoring.query_dsl.types")
_validator: Any = import_module("backend.02_features.05_monitoring.query_dsl.validator")
_compiler: Any = import_module("backend.02_features.05_monitoring.query_dsl.compiler")

Timerange = _types.Timerange
Filter = _types.Filter
FieldValue = _types.FieldValue
FieldValues = _types.FieldValues
LogsQuery = _types.LogsQuery
MetricsQuery = _types.MetricsQuery
TracesQuery = _types.TracesQuery
LogRow = _types.LogRow
SpanRow = _types.SpanRow
TimeseriesPoint = _types.TimeseriesPoint
QueryResult = _types.QueryResult

InvalidQueryError = _validator.InvalidQueryError
validate_logs_query = _validator.validate_logs_query
validate_metrics_query = _validator.validate_metrics_query
validate_traces_query = _validator.validate_traces_query

compile_logs_query = _compiler.compile_logs_query
compile_metrics_query = _compiler.compile_metrics_query
compile_traces_query = _compiler.compile_traces_query
compile_trace_detail = _compiler.compile_trace_detail
compile_filter = _compiler.compile_filter
encode_cursor = _compiler.encode_cursor
decode_cursor = _compiler.decode_cursor

__all__ = [
    "Timerange", "Filter", "FieldValue", "FieldValues",
    "LogsQuery", "MetricsQuery", "TracesQuery",
    "LogRow", "SpanRow", "TimeseriesPoint", "QueryResult",
    "InvalidQueryError",
    "validate_logs_query", "validate_metrics_query", "validate_traces_query",
    "compile_logs_query", "compile_metrics_query", "compile_traces_query",
    "compile_trace_detail", "compile_filter",
    "encode_cursor", "decode_cursor",
]
