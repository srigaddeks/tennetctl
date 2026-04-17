"""Tests for the alert events list/detail API (13-08b).

Seeds evt_monitoring_alert_events rows directly and exercises the
/v1/monitoring/alerts list + detail endpoints.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-000e-7000-0000-000000000001"
_WS_ID = "019e0808-000e-7000-0000-000000000002"
_USER_ID = "019e0808-000e-7000-0000-000000000003"
_SESSION_ID = "019e0808-000e-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as c:
        await c.execute(
            'DELETE FROM "05_monitoring"."60_evt_monitoring_alert_events" WHERE org_id=$1',
            _ORG_ID,
        )
        await c.execute(
            'DELETE FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1',
            _ORG_ID,
        )


async def _seed_rule_and_events(pool: Any) -> dict[str, Any]:
    rule_id = _core_id.uuid7()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
                (id, org_id, name, description, target, dsl, condition, severity_id,
                 notify_template_key, labels, is_active, created_at, updated_at)
            VALUES ($1,$2,'api-evt','','metrics',$3::jsonb,$4::jsonb,4,'alert.test','{}'::jsonb,TRUE,$5,$5)
            """,
            rule_id, _ORG_ID,
            json.dumps({"target": "metrics", "metric_key": "x",
                        "timerange": {"last": "5m"}, "aggregate": "sum", "bucket": "1m"}),
            json.dumps({"op": "gt", "threshold": 0.0, "for_duration_seconds": 0}),
            now,
        )
        # One firing event.
        e1_id = _core_id.uuid7()
        await c.execute(
            """
            INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
                (id, rule_id, fingerprint, state, value, threshold, org_id,
                 started_at, labels)
            VALUES ($1,$2,'fp-a','firing',10.0,5.0,$3,$4,'{}'::jsonb)
            """,
            e1_id, rule_id, _ORG_ID, now,
        )
        # One resolved event.
        e2_id = _core_id.uuid7()
        await c.execute(
            """
            INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
                (id, rule_id, fingerprint, state, value, threshold, org_id,
                 started_at, resolved_at, labels)
            VALUES ($1,$2,'fp-b','resolved',3.0,5.0,$3,$4,$5,'{}'::jsonb)
            """,
            e2_id, rule_id, _ORG_ID, now - timedelta(minutes=5), now - timedelta(minutes=1),
        )
    return {"rule_id": rule_id, "e1_id": e1_id, "e2_id": e2_id, "e1_started_at": now}


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(
                transport=transport, base_url="http://test", headers=_HDR,
            ) as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_list_alerts_filters_by_state_firing(live_app):
    client, pool = live_app
    seeded = await _seed_rule_and_events(pool)
    r = await client.get("/v1/monitoring/alerts?state=firing")
    assert r.status_code == 200, r.text
    items = r.json()["data"]["items"]
    ids = {i["id"] for i in items}
    assert seeded["e1_id"] in ids
    assert seeded["e2_id"] not in ids


@pytest.mark.asyncio
async def test_list_alerts_filters_by_severity(live_app):
    client, pool = live_app
    await _seed_rule_and_events(pool)
    r = await client.get("/v1/monitoring/alerts?severity=critical")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    # Rule was seeded with severity_id=3 (critical).
    assert all(i["severity"] == "critical" for i in items)
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_get_alert_detail(live_app):
    client, pool = live_app
    seeded = await _seed_rule_and_events(pool)
    started = seeded["e1_started_at"].isoformat()
    r = await client.get(
        f"/v1/monitoring/alerts/{seeded['e1_id']}?started_at={started}",
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["id"] == seeded["e1_id"]
    assert data["state"] == "firing"
    assert data["fingerprint"] == "fp-a"
