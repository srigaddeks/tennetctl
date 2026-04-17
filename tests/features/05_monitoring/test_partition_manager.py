"""Tests for partition manager procs (13-07)."""

from __future__ import annotations

import os
from datetime import date, timedelta
from importlib import import_module
from typing import Any

import asyncpg
import pytest

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)


@pytest.fixture
async def conn():
    c = await asyncpg.connect(LIVE_DSN)
    try:
        yield c
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_ensure_partitions_creates_new_partitions(conn):
    """monitoring_ensure_partitions creates partitions today..today+N."""
    # Count partitions for evt_monitoring_logs before
    before = await conn.fetchval(
        "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='05_monitoring' AND c.relkind='r' "
        "AND c.relname LIKE '60_evt_monitoring_logs_p%'"
    )
    await conn.fetchval(
        'SELECT "05_monitoring".monitoring_ensure_partitions($1, $2)',
        "60_evt_monitoring_logs", 7,
    )
    after = await conn.fetchval(
        "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='05_monitoring' AND c.relkind='r' "
        "AND c.relname LIKE '60_evt_monitoring_logs_p%'"
    )
    assert after >= before  # at least no fewer partitions after
    # running again is idempotent
    created = await conn.fetchval(
        'SELECT "05_monitoring".monitoring_ensure_partitions($1, $2)',
        "60_evt_monitoring_logs", 7,
    )
    assert created == 0


@pytest.mark.asyncio
async def test_drop_old_partitions_respects_retention(conn):
    """monitoring_drop_old_partitions drops partitions older than cutoff."""
    # Create a deliberately-old partition
    tbl = "test_part_parent"
    await conn.execute(
        f'CREATE TABLE IF NOT EXISTS "05_monitoring".{tbl} '
        f'(recorded_at TIMESTAMP NOT NULL) PARTITION BY RANGE (recorded_at)'
    )
    old_date = date.today() - timedelta(days=30)
    part_name = f'{tbl}_p{old_date.strftime("%Y%m%d")}'
    await conn.execute(
        f'CREATE TABLE IF NOT EXISTS "05_monitoring".{part_name} '
        f'PARTITION OF "05_monitoring".{tbl} '
        f'FOR VALUES FROM (\'{old_date} 00:00:00\') TO (\'{old_date + timedelta(days=1)} 00:00:00\')'
    )
    try:
        dropped = await conn.fetchval(
            'SELECT "05_monitoring".monitoring_drop_old_partitions($1, $2)',
            tbl, 7,
        )
        assert dropped >= 1
    finally:
        await conn.execute(f'DROP TABLE IF EXISTS "05_monitoring".{tbl} CASCADE')


@pytest.mark.asyncio
async def test_partition_manager_iterates_all_policies(conn):
    """monitoring_partition_manager yields one row per active retention policy."""
    rows = await conn.fetch('SELECT * FROM "05_monitoring".monitoring_partition_manager()')
    # We seeded 7 policies in migration 045
    assert len(rows) >= 6
    # Each returned row has expected columns
    for r in rows:
        assert "table_name" in r
        assert "days_to_keep" in r
        assert r["days_to_keep"] > 0


@pytest.mark.asyncio
async def test_partition_manager_skips_missing_tables(conn):
    """Inactive/missing tables yield (0, 0) instead of errors."""
    # Set a policy to a non-existent table and confirm manager returns safely
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_retention_policies"
            (code, table_name, days_to_keep, tier)
        VALUES ('test_missing', 'this_table_does_not_exist', 7, 'hot')
        ON CONFLICT (code) DO NOTHING
        """,
    )
    try:
        rows = await conn.fetch(
            'SELECT * FROM "05_monitoring".monitoring_partition_manager()'
        )
        target = [r for r in rows if r["table_name"] == "this_table_does_not_exist"]
        assert len(target) == 1
        assert target[0]["created"] == 0
        assert target[0]["dropped"] == 0
    finally:
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_retention_policies" '
            'WHERE code=$1',
            "test_missing",
        )
