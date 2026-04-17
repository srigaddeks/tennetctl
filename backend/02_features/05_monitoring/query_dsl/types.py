"""Pydantic models for the Monitoring Query DSL.

See ADR-029. Security-critical: these types are the grammar. All user-facing
validation for the DSL happens through Pydantic here; the compiler trusts the
validator output.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Max range a timerange may span. See ADR-029 (security model).
MAX_RANGE_DAYS = 90

# Regex limiter. See ADR-029.
REGEX_MAX_LEN = 100
# Nested quantifier patterns that blow up with catastrophic backtracking.
NESTED_QUANT_PATTERNS = ("(a+)+", "(a*)*", "(a+)*", "(a*)+")

# Bucket -> resolved seconds (for metrics time-bucketing).
BUCKET_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "1h": 3600,
    "1d": 86400,
}

# "last" token -> timedelta.
LAST_TOKENS: dict[str, timedelta] = {
    "15m": timedelta(minutes=15),
    "1h":  timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d":  timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}


# ── Timerange ──────────────────────────────────────────────────────────

class Timerange(BaseModel):
    """Either an absolute (from_ts, to_ts) range or a `last` token."""
    model_config = ConfigDict(extra="forbid")

    from_ts: datetime | None = None
    to_ts: datetime | None = None
    last: Literal["15m", "1h", "24h", "7d", "30d", "90d"] | None = None

    @model_validator(mode="after")
    def _check_shape(self) -> "Timerange":
        if self.last is not None:
            if self.from_ts is not None or self.to_ts is not None:
                raise ValueError(
                    "timerange: cannot mix `last` with `from_ts`/`to_ts`",
                )
            return self
        # absolute mode
        if self.from_ts is None and self.to_ts is None:
            raise ValueError(
                "timerange: must provide either `last` or (`from_ts`,`to_ts`)",
            )
        if self.from_ts is not None and self.to_ts is not None:
            if self.to_ts <= self.from_ts:
                raise ValueError("timerange: `to_ts` must be strictly after `from_ts`")
            span = self.to_ts - self.from_ts
            if span > timedelta(days=MAX_RANGE_DAYS):
                raise ValueError(
                    f"timerange span exceeds {MAX_RANGE_DAYS}d cap",
                )
        return self

    def resolve(self, now: datetime | None = None) -> tuple[datetime, datetime]:
        """Return absolute (from_ts, to_ts). Naive UTC datetimes."""
        cur = now or datetime.now(timezone.utc).replace(tzinfo=None)
        if cur.tzinfo is not None:
            cur = cur.astimezone(timezone.utc).replace(tzinfo=None)
        if self.last is not None:
            delta = LAST_TOKENS[self.last]
            return cur - delta, cur
        assert self.from_ts is not None  # model_validator guarantees
        to_ts = self.to_ts or cur
        from_ts = self.from_ts
        # Strip tzinfo — we work in UTC-naive.
        if from_ts.tzinfo is not None:
            from_ts = from_ts.astimezone(timezone.utc).replace(tzinfo=None)
        if to_ts.tzinfo is not None:
            to_ts = to_ts.astimezone(timezone.utc).replace(tzinfo=None)
        return from_ts, to_ts


# ── Filter tree ────────────────────────────────────────────────────────

FilterOp = Literal[
    "eq", "ne", "in", "nin", "lt", "lte", "gt", "gte",
    "contains", "jsonb_path", "regex_limited",
]


class FieldValue(BaseModel):
    """Leaf operator payload: {field, value}."""
    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1, max_length=100)
    value: Any


class FieldValues(BaseModel):
    """Leaf operator payload for `in`/`nin`: {field, values}."""
    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1, max_length=100)
    values: list[Any] = Field(min_length=1, max_length=500)


class Filter(BaseModel):
    """Recursive filter tree. Exactly one of the fields must be set on any node."""
    model_config = ConfigDict(extra="forbid")

    and_: list["Filter"] | None = Field(default=None, alias="and")
    or_:  list["Filter"] | None = Field(default=None, alias="or")
    not_: "Filter | None" = Field(default=None, alias="not")
    eq:   FieldValue | None = None
    ne:   FieldValue | None = None
    in_:  FieldValues | None = Field(default=None, alias="in")
    nin:  FieldValues | None = None
    lt:   FieldValue | None = None
    lte:  FieldValue | None = None
    gt:   FieldValue | None = None
    gte:  FieldValue | None = None
    contains:      FieldValue | None = None
    jsonb_path:    FieldValue | None = None
    regex_limited: FieldValue | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "Filter":
        set_names = [n for n, v in self._iter_fields() if v is not None]
        if len(set_names) != 1:
            raise ValueError(
                f"Filter node must have exactly one operator set (got {set_names})",
            )
        # Regex-limited validation: length + nested quantifier defense.
        if self.regex_limited is not None:
            val = self.regex_limited.value
            if not isinstance(val, str):
                raise ValueError("regex_limited.value must be a string")
            if len(val) > REGEX_MAX_LEN:
                raise ValueError(
                    f"regex_limited.value exceeds {REGEX_MAX_LEN} chars",
                )
            for bad in NESTED_QUANT_PATTERNS:
                if bad in val:
                    raise ValueError(
                        f"regex_limited: nested quantifier pattern rejected (ReDoS defense)",
                    )
        return self

    def _iter_fields(self) -> list[tuple[str, Any]]:
        return [
            ("and", self.and_), ("or", self.or_), ("not", self.not_),
            ("eq", self.eq), ("ne", self.ne), ("in", self.in_), ("nin", self.nin),
            ("lt", self.lt), ("lte", self.lte), ("gt", self.gt), ("gte", self.gte),
            ("contains", self.contains), ("jsonb_path", self.jsonb_path),
            ("regex_limited", self.regex_limited),
        ]


Filter.model_rebuild()


# ── Target queries ────────────────────────────────────────────────────

class LogsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Literal["logs"] = "logs"
    filter: Filter | None = None
    timerange: Timerange
    severity_min: int | None = Field(default=None, ge=0, le=24)
    body_contains: str | None = Field(default=None, min_length=1, max_length=500)
    trace_id: str | None = Field(default=None, min_length=1, max_length=64)
    limit: int = Field(default=100, ge=1, le=1000)
    cursor: str | None = None


MetricAggregate = Literal["sum", "avg", "min", "max", "count", "rate", "p50", "p95", "p99"]
MetricBucket = Literal["1m", "5m", "1h", "1d"]


class MetricsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Literal["metrics"] = "metrics"
    metric_key: str = Field(min_length=1, max_length=200)
    labels: dict[str, str] | None = None
    filter: Filter | None = None
    timerange: Timerange
    aggregate: MetricAggregate = "sum"
    bucket: MetricBucket | None = "1m"
    groupby: list[str] | None = Field(default=None, max_length=10)
    limit: int = Field(default=1000, ge=1, le=10000)


class TracesQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Literal["traces"] = "traces"
    filter: Filter | None = None
    timerange: Timerange
    service_name: str | None = Field(default=None, min_length=1, max_length=200)
    span_name_contains: str | None = Field(default=None, min_length=1, max_length=200)
    duration_min_ms: float | None = Field(default=None, ge=0)
    duration_max_ms: float | None = Field(default=None, ge=0)
    has_error: bool | None = None
    trace_id: str | None = Field(default=None, min_length=1, max_length=64)
    limit: int = Field(default=100, ge=1, le=1000)
    cursor: str | None = None


# ── Response shapes ──────────────────────────────────────────────────

class LogRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    recorded_at: datetime
    severity_id: int
    severity_code: str | None = None
    body: str
    service_name: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    attributes: dict[str, Any] | list[Any] | None = None


class TimeseriesPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bucket_ts: datetime
    value: float | None = None
    group: dict[str, Any] | None = None


class SpanRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    recorded_at: datetime
    name: str
    kind_code: str | None = None
    status_code: str | None = None
    duration_ns: int | None = None
    service_name: str | None = None


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[Any]
    next_cursor: str | None = None


__all__ = [
    "Timerange", "Filter", "FieldValue", "FieldValues",
    "LogsQuery", "MetricsQuery", "TracesQuery",
    "LogRow", "TimeseriesPoint", "SpanRow", "QueryResult",
    "MAX_RANGE_DAYS", "REGEX_MAX_LEN", "BUCKET_SECONDS", "LAST_TOKENS",
]
