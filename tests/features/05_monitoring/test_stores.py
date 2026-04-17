"""Tests for monitoring Postgres stores — logs, metrics, spans, resources."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any
from uuid import uuid4

import pytest

# Import stores via importlib (numeric-prefix dirs).
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")
_logs_mod: Any = import_module("backend.02_features.05_monitoring.stores.postgres_logs_store")
_metrics_mod: Any = import_module("backend.02_features.05_monitoring.stores.postgres_metrics_store")
_spans_mod: Any = import_module("backend.02_features.05_monitoring.stores.postgres_spans_store")
_resources_mod: Any = import_module("backend.02_features.05_monitoring.stores.postgres_resources_store")

PostgresLogsStore = _logs_mod.PostgresLogsStore
PostgresMetricsStore = _metrics_mod.PostgresMetricsStore
PostgresSpansStore = _spans_mod.PostgresSpansStore
PostgresResourcesStore = _resources_mod.PostgresResourcesStore
compute_resource_hash = _resources_mod.compute_resource_hash


LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

# Collect all the ephemeral org_ids used here so we can clean up after.
_TEST_ORG_IDS = (
    "org-a", "org-logs-1", "org-logs-pg",
    "org-m1", "org-m-cnt", "org-m-g", "org-m-h", "org-m-card",
    "org-s1", "org-r-1", "org-r-2",
)


@pytest.fixture
async def db_conn():
    """Override conftest's test-DB fixture — monitoring tests need the LIVE DB where schema exists."""
    import asyncpg
    conn = await asyncpg.connect(LIVE_DSN)
    # asyncpg dict→jsonb codec (matches backend.01_core.database.create_pool init).
    import json
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    try:
        yield conn
    finally:
        # Clean up test rows by org_id scope.
        try:
            await conn.execute(
                'DELETE FROM "05_monitoring"."61_evt_monitoring_metric_points" '
                'WHERE org_id = ANY($1::text[])',
                list(_TEST_ORG_IDS),
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."60_evt_monitoring_logs" '
                'WHERE org_id = ANY($1::text[])',
                list(_TEST_ORG_IDS),
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."62_evt_monitoring_spans" '
                'WHERE org_id = ANY($1::text[])',
                list(_TEST_ORG_IDS),
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."10_fct_monitoring_metrics" '
                'WHERE org_id = ANY($1::text[])',
                list(_TEST_ORG_IDS),
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" '
                'WHERE org_id = ANY($1::text[])',
                list(_TEST_ORG_IDS),
            )
        finally:
            await conn.close()


async def _make_resource(conn: Any, org_id: str = "org-a") -> int:
    store = PostgresResourcesStore(pool=None)
    return await store.upsert(
        conn,
        _types.ResourceRecord(
            org_id=org_id,
            service_name="tennetctl-tests",
            service_instance_id="i-001",
            service_version="0.0.0",
            attributes={"env": "test"},
        ),
    )


async def _cleanup_metric(conn: Any, metric_id: int) -> None:
    await conn.execute(
        'DELETE FROM "05_monitoring"."61_evt_monitoring_metric_points" WHERE metric_id = $1',
        metric_id,
    )


# --------------------------- Logs ---------------------------

async def test_logs_insert_batch_and_query(db_conn):
    store = PostgresLogsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-logs-1")
    now = datetime(2026, 4, 17, 12, 0, 0)
    records = [
        _types.LogRecord(
            id=str(uuid4()),
            org_id="org-logs-1",
            resource_id=resource_id,
            recorded_at=now + timedelta(seconds=i),
            observed_at=now + timedelta(seconds=i),
            severity_id=9,
            body=f"hello {i}",
            trace_id="t1" if i == 0 else None,
        )
        for i in range(5)
    ]
    n = await store.insert_batch(db_conn, records)
    assert n == 5

    rows = await store.query(
        db_conn, _types.LogQuery(org_id="org-logs-1", severity_min=9, limit=10),
    )
    assert len(rows) >= 5
    # Test trace_id filter
    trace_rows = await store.query(
        db_conn, _types.LogQuery(org_id="org-logs-1", trace_id="t1"),
    )
    assert len(trace_rows) == 1
    # Test body_contains
    body_rows = await store.query(
        db_conn, _types.LogQuery(org_id="org-logs-1", body_contains="hello 2"),
    )
    assert len(body_rows) == 1


async def test_logs_cursor_pagination(db_conn):
    store = PostgresLogsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-logs-pg")
    now = datetime(2026, 4, 17, 13, 0, 0)
    records = [
        _types.LogRecord(
            id=str(uuid4()),
            org_id="org-logs-pg",
            resource_id=resource_id,
            recorded_at=now + timedelta(seconds=i),
            observed_at=now + timedelta(seconds=i),
            severity_id=9,
            body=f"page {i}",
        )
        for i in range(10)
    ]
    await store.insert_batch(db_conn, records)

    page1 = await store.query(db_conn, _types.LogQuery(org_id="org-logs-pg", limit=3))
    assert len(page1) == 3
    last = page1[-1]
    page2 = await store.query(
        db_conn,
        _types.LogQuery(
            org_id="org-logs-pg",
            limit=3,
            cursor_recorded_at=last["recorded_at"],
            cursor_id=last["id"],
        ),
    )
    assert len(page2) == 3
    p1_ids = {r["id"] for r in page1}
    p2_ids = {r["id"] for r in page2}
    assert not (p1_ids & p2_ids)


# ------------------------- Metrics --------------------------

async def test_metrics_register_idempotent(db_conn):
    store = PostgresMetricsStore(pool=None)
    m = _types.MetricDef(org_id="org-m1", key="test.register.x", kind_id=1)
    id1 = await store.register(db_conn, m)
    id2 = await store.register(db_conn, m)
    assert id1 == id2


async def test_metrics_counter_increment_and_timeseries(db_conn):
    store = PostgresMetricsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-m-cnt")
    metric_id = await store.register(
        db_conn,
        _types.MetricDef(org_id="org-m-cnt", key="test.counter", kind_id=1, max_cardinality=50),
    )
    await _cleanup_metric(db_conn, metric_id)
    # Reset in-memory cardinality cache since the DB rows were just deleted.
    store._card_cache.pop(metric_id, None)
    now = datetime(2026, 4, 17, 14, 0, 0)
    for i in range(3):
        ok = await store.increment(
            db_conn, metric_id, {"route": "/v1/x"}, 1.0,
            resource_id=resource_id, org_id="org-m-cnt", recorded_at=now + timedelta(seconds=i),
        )
        assert ok
    series = await store.query_timeseries(
        db_conn, metric_id, {"route": "/v1/x"}, "minute",
        from_ts=now - timedelta(minutes=1),
        to_ts=now + timedelta(minutes=1),
    )
    assert series
    assert sum(int(r["count"]) for r in series) == 3


async def test_metrics_gauge_set_and_latest(db_conn):
    store = PostgresMetricsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-m-g")
    metric_id = await store.register(
        db_conn, _types.MetricDef(org_id="org-m-g", key="test.gauge", kind_id=2),
    )
    await _cleanup_metric(db_conn, metric_id)
    store._card_cache.pop(metric_id, None)
    now = datetime(2026, 4, 17, 14, 30, 0)
    await store.set_gauge(
        db_conn, metric_id, {"host": "h1"}, 10.0,
        resource_id=resource_id, org_id="org-m-g", recorded_at=now,
    )
    await store.set_gauge(
        db_conn, metric_id, {"host": "h1"}, 42.0,
        resource_id=resource_id, org_id="org-m-g",
        recorded_at=now + timedelta(seconds=10),
    )
    latest = await store.query_latest(db_conn, metric_id, {"host": "h1"})
    assert latest is not None
    assert latest["value"] == 42.0


async def test_metrics_histogram_observe_buckets(db_conn):
    store = PostgresMetricsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-m-h")
    metric_id = await store.register(
        db_conn,
        _types.MetricDef(
            org_id="org-m-h", key="test.histogram", kind_id=3,
            histogram_buckets=[1.0, 5.0, 10.0],
        ),
    )
    await _cleanup_metric(db_conn, metric_id)
    store._card_cache.pop(metric_id, None)
    now = datetime(2026, 4, 17, 14, 45, 0)
    await store.observe_histogram(
        db_conn, metric_id, {}, 0.5,
        resource_id=resource_id, org_id="org-m-h", recorded_at=now,
    )
    row = await db_conn.fetchrow(
        'SELECT histogram_counts, histogram_sum, histogram_count '
        'FROM "05_monitoring"."61_evt_monitoring_metric_points" '
        'WHERE metric_id = $1 ORDER BY recorded_at DESC LIMIT 1',
        metric_id,
    )
    assert row is not None
    counts = list(row["histogram_counts"])
    # 0.5 lands in first bucket (<= 1.0)
    assert counts[0] == 1
    assert sum(counts) == 1
    assert row["histogram_count"] == 1


async def test_metrics_cardinality_reject(db_conn):
    store = PostgresMetricsStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-m-card")
    metric_id = await store.register(
        db_conn,
        _types.MetricDef(
            org_id="org-m-card", key="test.card", kind_id=1, max_cardinality=2,
        ),
    )
    await _cleanup_metric(db_conn, metric_id)
    store._card_cache.pop(metric_id, None)
    now = datetime(2026, 4, 17, 15, 0, 0)
    assert await store.increment(
        db_conn, metric_id, {"k": "a"}, 1.0,
        resource_id=resource_id, org_id="org-m-card", recorded_at=now,
    )
    assert await store.increment(
        db_conn, metric_id, {"k": "b"}, 1.0,
        resource_id=resource_id, org_id="org-m-card",
        recorded_at=now + timedelta(seconds=1),
    )
    # Third distinct label combo → reject.
    accepted = await store.increment(
        db_conn, metric_id, {"k": "c"}, 1.0,
        resource_id=resource_id, org_id="org-m-card",
        recorded_at=now + timedelta(seconds=2),
    )
    assert accepted is False
    # But an existing combo still works.
    assert await store.increment(
        db_conn, metric_id, {"k": "a"}, 1.0,
        resource_id=resource_id, org_id="org-m-card",
        recorded_at=now + timedelta(seconds=3),
    )


# -------------------------- Spans ---------------------------

async def test_spans_insert_and_query_by_trace(db_conn):
    store = PostgresSpansStore(pool=None)
    resource_id = await _make_resource(db_conn, org_id="org-s1")
    trace_id = "abc" + uuid4().hex[:13]
    recorded = datetime(2026, 4, 17, 16, 0, 0)
    spans = [
        _types.SpanRecord(
            trace_id=trace_id, span_id=f"s{i:02x}{uuid4().hex[:14]}",
            parent_span_id=None if i == 0 else f"s{(i-1):02x}",
            org_id="org-s1", resource_id=resource_id,
            name=f"op{i}", kind_id=1, status_id=1,
            recorded_at=recorded + timedelta(milliseconds=i * 10),
            start_time_unix_nano=1_000_000_000 * i,
            end_time_unix_nano=1_000_000_000 * i + 5_000_000,
        )
        for i in range(3)
    ]
    n = await store.insert_batch(db_conn, spans)
    assert n == 3
    rows = await store.query_by_trace(db_conn, trace_id)
    assert len(rows) == 3
    assert all(int(r["duration_ns"]) == 5_000_000 for r in rows)
    # Ordered by start_time ascending.
    starts = [int(r["start_time_unix_nano"]) for r in rows]
    assert starts == sorted(starts)


# ------------------------- Resources ------------------------

async def test_resources_upsert_idempotent(db_conn):
    store = PostgresResourcesStore(pool=None)
    rec = _types.ResourceRecord(
        org_id="org-r-1",
        service_name="svc-a",
        service_instance_id="inst-1",
        service_version="1.0",
        attributes={"k": "v"},
    )
    id1 = await store.upsert(db_conn, rec)
    id2 = await store.upsert(db_conn, rec)
    assert id1 == id2


async def test_resources_upsert_new_hash_new_row(db_conn):
    store = PostgresResourcesStore(pool=None)
    a = _types.ResourceRecord(org_id="org-r-2", service_name="svc-x", attributes={"a": 1})
    b = _types.ResourceRecord(org_id="org-r-2", service_name="svc-y", attributes={"a": 1})
    id_a = await store.upsert(db_conn, a)
    id_b = await store.upsert(db_conn, b)
    assert id_a != id_b


async def test_resources_hash_deterministic():
    h1 = compute_resource_hash("svc", "i1", "1.0", {"b": 2, "a": 1})
    h2 = compute_resource_hash("svc", "i1", "1.0", {"a": 1, "b": 2})
    assert h1 == h2
    h3 = compute_resource_hash("svc", "i1", "1.0", {"a": 1})
    assert h1 != h3
