"""Shared dataclasses for monitoring stores — frozen, immutable."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ResourceRecord:
    """Interned OTel resource identity."""
    org_id: str
    service_name: str
    service_instance_id: str | None = None
    service_version: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LogRecord:
    id: str
    org_id: str
    resource_id: int
    recorded_at: datetime
    observed_at: datetime
    severity_id: int
    body: str
    workspace_id: str | None = None
    severity_text: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    trace_flags: int | None = None
    scope_name: str | None = None
    scope_version: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    dropped_attributes_count: int = 0


@dataclass(frozen=True)
class LogQuery:
    org_id: str
    from_ts: datetime | None = None
    to_ts: datetime | None = None
    severity_min: int | None = None
    trace_id: str | None = None
    body_contains: str | None = None
    limit: int = 100
    # Cursor pagination: (recorded_at, id) from the last row of previous page.
    cursor_recorded_at: datetime | None = None
    cursor_id: str | None = None


@dataclass(frozen=True)
class MetricDef:
    org_id: str
    key: str
    kind_id: int   # 1=counter, 2=gauge, 3=histogram
    label_keys: list[str] = field(default_factory=list)
    histogram_buckets: list[float] | None = None
    max_cardinality: int = 1000
    description: str = ""
    unit: str = ""


@dataclass(frozen=True)
class MetricPoint:
    metric_id: int
    resource_id: int
    org_id: str
    recorded_at: datetime
    labels: dict[str, Any] = field(default_factory=dict)
    workspace_id: str | None = None
    value: float | None = None
    histogram_counts: list[int] | None = None
    histogram_sum: float | None = None
    histogram_count: int | None = None
    trace_id: str | None = None
    span_id: str | None = None


@dataclass(frozen=True)
class TimeseriesPoint:
    bucket: datetime
    value: float
    count: int


@dataclass(frozen=True)
class TimeseriesResult:
    metric_id: int
    points: list[TimeseriesPoint]


@dataclass(frozen=True)
class SpanRecord:
    trace_id: str
    span_id: str
    org_id: str
    resource_id: int
    name: str
    kind_id: int
    status_id: int
    recorded_at: datetime
    start_time_unix_nano: int
    end_time_unix_nano: int
    parent_span_id: str | None = None
    workspace_id: str | None = None
    status_message: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[Any] = field(default_factory=list)
    links: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class SpanQuery:
    org_id: str
    from_ts: datetime | None = None
    to_ts: datetime | None = None
    service_name: str | None = None
    name_contains: str | None = None
    status_id: int | None = None
    limit: int = 100
