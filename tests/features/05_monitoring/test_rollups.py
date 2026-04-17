"""Tests for monitoring rollup procs (13-07)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import asyncpg
import pytest

_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0707-0001-7000-0000-000000000001"


def _now_min() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)


async def _ensure_metric(conn: Any, key: str) -> int:
    # insert a metric row; reuse if exists
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."10_fct_monitoring_metrics" '
        'WHERE org_id=$1 AND key=$2',
        _ORG_ID, key,
    )
    if row:
        return row["id"]
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_metrics"
            (org_id, key, kind_id, label_keys, description, unit,
             histogram_buckets, max_cardinality, created_at, updated_at)
        VALUES ($1,$2,1,ARRAY[]::TEXT[],'test','1',NULL,1000,
                CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        ON CONFLICT DO NOTHING
        """,
        _ORG_ID, key,
    )
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."10_fct_monitoring_metrics" '
        'WHERE org_id=$1 AND key=$2',
        _ORG_ID, key,
    )
    return row["id"]


async def _ensure_resource(conn: Any) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."11_fct_monitoring_resources" '
        'WHERE org_id=$1 AND service_name=$2 LIMIT 1',
        _ORG_ID, "rollup-test",
    )
    if row:
        return row["id"]
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."11_fct_monitoring_resources"
            (org_id, service_name, service_instance_id, service_version,
             attributes, resource_hash, created_at)
        VALUES ($1,'rollup-test','inst-1','v1','{}'::jsonb,
                decode('00','hex'),CURRENT_TIMESTAMP)
        ON CONFLICT DO NOTHING
        """,
        _ORG_ID,
    )
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."11_fct_monitoring_resources" '
        'WHERE org_id=$1 AND service_name=$2 LIMIT 1',
        _ORG_ID, "rollup-test",
    )
    return row["id"]


async def _cleanup(conn: Any) -> None:
    await conn.execute(
        'DELETE FROM "05_monitoring"."70_evt_monitoring_metric_points_1m" WHERE org_id=$1',
        _ORG_ID,
    )
    await conn.execute(
        'DELETE FROM "05_monitoring"."61_evt_monitoring_metric_points" WHERE org_id=$1',
        _ORG_ID,
    )


@pytest.fixture
async def conn():
    c = await asyncpg.connect(LIVE_DSN)
    try:
        await _cleanup(c)
        yield c
        await _cleanup(c)
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_rollup_1m_basic_aggregation(conn):
    metric_id = await _ensure_metric(conn, "test.rollup.counter")
    resource_id = await _ensure_resource(conn)
    bucket = _now_min() - timedelta(minutes=5)
    # insert 3 points in the same minute
    for i in range(3):
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, value, recorded_at)
            VALUES ($1,$2,$3,'{}'::jsonb,$4,$5)
            """,
            metric_id, resource_id, _ORG_ID, float(i + 1),
            bucket + timedelta(seconds=i * 10),
        )
    rows = await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m($1)', bucket - timedelta(minutes=1))
    assert rows is not None
    agg = await conn.fetchrow(
        'SELECT count, sum, min, max FROM "05_monitoring"."70_evt_monitoring_metric_points_1m" '
        'WHERE metric_id=$1 AND bucket=$2',
        metric_id, bucket,
    )
    assert agg is not None
    assert agg["count"] == 3
    assert agg["sum"] == pytest.approx(6.0)
    assert agg["min"] == pytest.approx(1.0)
    assert agg["max"] == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_rollup_1m_idempotent(conn):
    metric_id = await _ensure_metric(conn, "test.rollup.idempotent")
    resource_id = await _ensure_resource(conn)
    bucket = _now_min() - timedelta(minutes=5)
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
            (metric_id, resource_id, org_id, labels, value, recorded_at)
        VALUES ($1,$2,$3,'{}'::jsonb,42.0,$4)
        """,
        metric_id, resource_id, _ORG_ID, bucket + timedelta(seconds=5),
    )
    # Run twice
    await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m($1)', bucket - timedelta(minutes=1))
    await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m($1)', bucket - timedelta(minutes=1))
    rows = await conn.fetch(
        'SELECT count FROM "05_monitoring"."70_evt_monitoring_metric_points_1m" '
        'WHERE metric_id=$1 AND bucket=$2',
        metric_id, bucket,
    )
    assert len(rows) == 1
    assert rows[0]["count"] == 1


@pytest.mark.asyncio
async def test_rollup_1m_histogram_elementwise_sum(conn):
    metric_id = await _ensure_metric(conn, "test.rollup.hist")
    resource_id = await _ensure_resource(conn)
    bucket = _now_min() - timedelta(minutes=5)
    # two histogram points with 4 buckets each (distinct recorded_at values)
    for i, arr in enumerate([[1, 2, 3, 4], [10, 20, 30, 40]]):
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, histogram_counts,
                 histogram_sum, histogram_count, recorded_at)
            VALUES ($1,$2,$3,'{}'::jsonb,$4::BIGINT[],0,0,$5)
            """,
            metric_id, resource_id, _ORG_ID, arr,
            bucket + timedelta(seconds=10 + i * 5),
        )
    await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m($1)', bucket - timedelta(minutes=1))
    row = await conn.fetchrow(
        'SELECT histogram_counts FROM "05_monitoring"."70_evt_monitoring_metric_points_1m" '
        'WHERE metric_id=$1 AND bucket=$2',
        metric_id, bucket,
    )
    assert row is not None
    # Element-wise sums: [11, 22, 33, 44]
    assert list(row["histogram_counts"]) == [11, 22, 33, 44]


@pytest.mark.asyncio
async def test_rollup_1m_gauge_uses_last(conn):
    metric_id = await _ensure_metric(conn, "test.rollup.gauge")
    resource_id = await _ensure_resource(conn)
    bucket = _now_min() - timedelta(minutes=5)
    # first value 1, last value 99 (recorded later within same minute bucket)
    for i, v in enumerate([1.0, 50.0, 99.0]):
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, value, recorded_at)
            VALUES ($1,$2,$3,'{}'::jsonb,$4,$5)
            """,
            metric_id, resource_id, _ORG_ID, v,
            bucket + timedelta(seconds=i * 10),
        )
    await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m($1)', bucket - timedelta(minutes=1))
    row = await conn.fetchrow(
        'SELECT last, sum, max FROM "05_monitoring"."70_evt_monitoring_metric_points_1m" '
        'WHERE metric_id=$1 AND bucket=$2',
        metric_id, bucket,
    )
    assert row["last"] == pytest.approx(99.0)
    assert row["sum"] == pytest.approx(150.0)
    assert row["max"] == pytest.approx(99.0)


@pytest.mark.asyncio
async def test_rollup_watermark_advances(conn):
    metric_id = await _ensure_metric(conn, "test.rollup.wm")
    resource_id = await _ensure_resource(conn)
    bucket = _now_min() - timedelta(minutes=5)
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
            (metric_id, resource_id, org_id, labels, value, recorded_at)
        VALUES ($1,$2,$3,'{}'::jsonb,7.0,$4)
        """,
        metric_id, resource_id, _ORG_ID, bucket + timedelta(seconds=5),
    )
    before = await conn.fetchval(
        'SELECT last_bucket FROM "05_monitoring"."20_dtl_monitoring_rollup_watermarks" '
        'WHERE table_name=$1',
        "70_evt_monitoring_metric_points_1m",
    )
    await conn.fetchval('SELECT "05_monitoring".monitoring_rollup_1m()')
    after = await conn.fetchval(
        'SELECT last_bucket FROM "05_monitoring"."20_dtl_monitoring_rollup_watermarks" '
        'WHERE table_name=$1',
        "70_evt_monitoring_metric_points_1m",
    )
    assert after >= before
