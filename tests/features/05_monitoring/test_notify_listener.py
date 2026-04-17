"""Tests for LISTEN/NOTIFY broadcaster + listener (13-07)."""

from __future__ import annotations

import asyncio
import os
from importlib import import_module
from typing import Any

import asyncpg
import pytest

_listener_mod: Any = import_module(
    "backend.02_features.05_monitoring.workers.notify_listener"
)
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0707-0007-7000-0000-000000000001"


@pytest.mark.asyncio
async def test_broadcaster_fans_out_and_drops_oldest():
    b = _listener_mod.Broadcaster(max_queue=3)
    q1 = b.subscribe()
    q2 = b.subscribe()
    for i in range(5):
        b.publish({"i": i})
    # each queue holds at most 3 items (drop-oldest when full)
    items1 = []
    items2 = []
    while not q1.empty():
        items1.append(q1.get_nowait())
    while not q2.empty():
        items2.append(q2.get_nowait())
    assert len(items1) == 3
    assert len(items2) == 3
    # newest items should be present
    assert items1[-1] == {"i": 4}


@pytest.mark.asyncio
async def test_notify_listener_receives_pg_notify():
    listener = _listener_mod.NotifyListener(LIVE_DSN)
    q = listener.broadcaster.subscribe()
    task = asyncio.create_task(listener.start())
    try:
        # Give it a beat to connect
        for _ in range(20):
            if listener._conn is not None:
                break
            await asyncio.sleep(0.1)
        assert listener._conn is not None, "notify listener failed to connect"

        # Insert a log row — trigger publishes NOTIFY.
        conn = await asyncpg.connect(LIVE_DSN)
        log_id = _core_id.uuid7()
        try:
            # Ensure a partition exists for today
            await conn.execute(
                'SELECT "05_monitoring".monitoring_ensure_partitions($1, $2)',
                "60_evt_monitoring_logs", 1,
            )
            # minimal resource + severity
            row = await conn.fetchrow(
                'SELECT id FROM "05_monitoring"."11_fct_monitoring_resources" '
                'WHERE org_id=$1 LIMIT 1',
                _ORG_ID,
            )
            if row is None:
                await conn.execute(
                    """
                    INSERT INTO "05_monitoring"."11_fct_monitoring_resources"
                        (org_id, service_name, service_instance_id, service_version,
                         attributes, resource_hash, created_at)
                    VALUES ($1,'notify-test','i','v','{}'::jsonb,
                            decode('01','hex'),CURRENT_TIMESTAMP)
                    """,
                    _ORG_ID,
                )
                row = await conn.fetchrow(
                    'SELECT id FROM "05_monitoring"."11_fct_monitoring_resources" '
                    'WHERE org_id=$1 LIMIT 1',
                    _ORG_ID,
                )
            resource_id = row["id"]
            await conn.execute(
                """
                INSERT INTO "05_monitoring"."60_evt_monitoring_logs"
                    (id, org_id, resource_id, recorded_at, observed_at,
                     severity_id, body, attributes, dropped_attributes_count)
                VALUES ($1,$2,$3,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,9,
                        'hello from notify test','{}'::jsonb,0)
                """,
                log_id, _ORG_ID, resource_id,
            )
            # Wait for NOTIFY to land on subscriber queue
            payload = await asyncio.wait_for(q.get(), timeout=5.0)
            assert payload.get("id") == log_id
            assert payload.get("org_id") == _ORG_ID
        finally:
            await conn.execute(
                'DELETE FROM "05_monitoring"."60_evt_monitoring_logs" WHERE id=$1',
                log_id,
            )
            await conn.close()
    finally:
        await listener.stop()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except Exception:  # noqa: BLE001
            pass


@pytest.mark.asyncio
async def test_broadcaster_unsubscribe():
    b = _listener_mod.Broadcaster(max_queue=5)
    q = b.subscribe()
    assert b.subscriber_count == 1
    b.unsubscribe(q)
    assert b.subscriber_count == 0
    # publishes after unsubscribe don't enqueue
    b.publish({"ignored": True})
    assert q.empty()
