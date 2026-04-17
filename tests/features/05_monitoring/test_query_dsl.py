"""Monitoring Query DSL — validator + compiler unit tests.

No database required — everything here is pure Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest

_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")


@dataclass
class _FakeCtx:
    org_id: str | None = "019e0000-9999-7000-0000-000000000001"
    workspace_id: str | None = None


def _now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_logs_compile_happy_path() -> None:
    q = _dsl.validate_logs_query({
        "target": "logs",
        "timerange": {"last": "1h"},
        "severity_min": 17,
        "body_contains": "error",
        "limit": 50,
    })
    sql, params = _dsl.compile_logs_query(q, _FakeCtx())
    assert 'FROM "05_monitoring"."v_monitoring_logs"' in sql
    assert "severity_id >=" in sql
    assert "body ILIKE" in sql
    # org_id was auto-bound from ctx
    assert _FakeCtx().org_id in params
    # limit is bound, not interpolated
    assert 50 in params


def test_metrics_compile_sum_avg_p95() -> None:
    for agg in ("sum", "avg", "p95"):
        q = _dsl.validate_metrics_query({
            "target": "metrics",
            "metric_key": "http.requests",
            "timerange": {"last": "24h"},
            "aggregate": agg,
            "bucket": "5m",
        })
        sql, params = _dsl.compile_metrics_query(q, _FakeCtx())
        assert "http.requests" in params
        assert "bucket_ts" in sql
        if agg == "p95":
            assert "percentile_cont" in sql


def test_traces_compile_with_filters() -> None:
    q = _dsl.validate_traces_query({
        "target": "traces",
        "timerange": {"last": "7d"},
        "service_name": "api",
        "span_name_contains": "GET",
        "duration_min_ms": 10,
        "has_error": True,
    })
    sql, params = _dsl.compile_traces_query(q, _FakeCtx())
    assert "service_name =" in sql
    assert "name ILIKE" in sql
    assert "duration_ns >=" in sql
    # 10 ms -> 10_000_000 ns bound.
    assert 10_000_000 in params
    assert "status_code = 'error'" in sql


def test_filter_tree_and_or_not_recursion() -> None:
    q = _dsl.validate_logs_query({
        "target": "logs",
        "timerange": {"last": "1h"},
        "filter": {
            "and": [
                {"eq": {"field": "service_name", "value": "api"}},
                {"or": [
                    {"eq": {"field": "severity_id", "value": 17}},
                    {"not": {"eq": {"field": "span_id", "value": "abc"}}},
                ]},
            ],
        },
    })
    sql, params = _dsl.compile_logs_query(q, _FakeCtx())
    assert "api" in params
    assert 17 in params
    assert "abc" in params
    # and/or/not structure reflected in SQL
    assert " AND " in sql
    assert " OR " in sql
    assert "NOT " in sql


def test_cursor_roundtrip() -> None:
    ts = datetime(2026, 4, 17, 12, 0, 0)
    row = {"recorded_at": ts, "id": "019e0000-aaaa-7000-0000-000000000001"}
    token = _dsl.encode_cursor(row)
    back = _dsl.decode_cursor(token)
    assert back is not None
    assert back[0] == ts
    assert back[1] == row["id"]


def test_sql_injection_value_parameterized() -> None:
    malicious = "'; DROP TABLE foo; --"
    q = _dsl.validate_logs_query({
        "target": "logs",
        "timerange": {"last": "1h"},
        "filter": {"eq": {"field": "body", "value": malicious}},
    })
    sql, params = _dsl.compile_logs_query(q, _FakeCtx())
    # Malicious value appears ONLY in params; SQL uses numbered placeholders.
    assert malicious in params
    assert "DROP TABLE" not in sql


def test_timerange_cap_rejects_over_90d() -> None:
    now = _now_utc_naive()
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.validate_logs_query({
            "target": "logs",
            "timerange": {
                "from_ts": (now - timedelta(days=120)).isoformat(),
                "to_ts": now.isoformat(),
            },
        })


def test_regex_limited_too_long() -> None:
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.validate_logs_query({
            "target": "logs",
            "timerange": {"last": "1h"},
            "filter": {"regex_limited": {"field": "body", "value": "a" * 101}},
        })


def test_regex_limited_nested_quantifier() -> None:
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.validate_logs_query({
            "target": "logs",
            "timerange": {"last": "1h"},
            "filter": {"regex_limited": {"field": "body", "value": "prefix(a+)+suffix"}},
        })


def test_filter_depth_cap() -> None:
    # Build a deeply nested filter — 12 levels of `not`.
    node: Any = {"eq": {"field": "body", "value": "x"}}
    for _ in range(12):
        node = {"not": node}
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.validate_logs_query({
            "target": "logs",
            "timerange": {"last": "1h"},
            "filter": node,
        })


def test_org_id_injected_from_ctx_not_body() -> None:
    q = _dsl.validate_logs_query({
        "target": "logs",
        "timerange": {"last": "1h"},
        "filter": {"eq": {"field": "org_id", "value": "other-org-trying-to-escape"}},
    })
    ctx = _FakeCtx(org_id="real-org-9999")
    _sql, params = _dsl.compile_logs_query(q, ctx)
    del _sql
    # ctx org_id MUST be bound; user value is bound too but the WHERE starts
    # with our injected clause.
    assert "real-org-9999" in params


def test_field_allowlist_rejects_unknown() -> None:
    q_dict = {
        "target": "logs",
        "timerange": {"last": "1h"},
        "filter": {"eq": {"field": "; DROP", "value": "x"}},
    }
    # The shape is valid Pydantic; compilation must reject the field.
    q = _dsl.validate_logs_query(q_dict)
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.compile_logs_query(q, _FakeCtx())


def test_metrics_invalid_label_key_rejected() -> None:
    q = _dsl.validate_metrics_query({
        "target": "metrics",
        "metric_key": "x",
        "timerange": {"last": "1h"},
        "labels": {"bad key!": "v"},
    })
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.compile_metrics_query(q, _FakeCtx())


def test_ctx_missing_org_rejected() -> None:
    q = _dsl.validate_logs_query({
        "target": "logs",
        "timerange": {"last": "1h"},
    })
    with pytest.raises(_dsl.InvalidQueryError):
        _dsl.compile_logs_query(q, _FakeCtx(org_id=None))
