"""Tests for silence matching logic (13-08b).

Exercises ``service.find_matching_silences`` + worker behaviour when a
matching silence is active.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest

_db: Any = import_module("backend.01_core.database")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)
_worker_mod: Any = import_module(
    "backend.02_features.05_monitoring.workers.alert_evaluator_worker"
)
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-000d-7000-0000-000000000001"
_USER_ID = "019e0808-000d-7000-0000-000000000099"


@pytest.fixture
async def pool():
    p = await _db.create_pool(LIVE_DSN, min_size=1, max_size=3)
    assert p is not None
    try:
        async with p.acquire() as conn:
            await _cleanup(conn)
        yield p
        async with p.acquire() as conn:
            await _cleanup(conn)
    finally:
        await p.close()


async def _cleanup(c: Any) -> None:
    await c.execute(
        'DELETE FROM "05_monitoring"."60_evt_monitoring_alert_events" WHERE org_id=$1',
        _ORG_ID,
    )
    await c.execute(
        'DELETE FROM "05_monitoring"."13_fct_monitoring_silences" WHERE org_id=$1',
        _ORG_ID,
    )
    await c.execute(
        'DELETE FROM "05_monitoring"."20_dtl_monitoring_rule_state" '
        'WHERE rule_id IN (SELECT id FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1)',
        _ORG_ID,
    )
    await c.execute(
        'DELETE FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1',
        _ORG_ID,
    )


async def _seed_silence(
    c: Any, *, rule_id: str | None = None, labels: dict[str, Any] | None = None,
    expired: bool = False,
) -> str:
    sid = _core_id.uuid7()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    starts = now - timedelta(hours=2) if expired else now - timedelta(minutes=1)
    ends = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    matcher: dict[str, Any] = {}
    if rule_id is not None:
        matcher["rule_id"] = rule_id
    if labels is not None:
        matcher["labels"] = labels
    await c.execute(
        """
        INSERT INTO "05_monitoring"."13_fct_monitoring_silences"
            (id, org_id, matcher, starts_at, ends_at, reason, created_by,
             is_active, created_at, updated_at)
        VALUES ($1,$2,$3::jsonb,$4,$5,'test',$6,TRUE,$7,$7)
        """,
        sid, _ORG_ID, json.dumps(matcher), starts, ends, _USER_ID, now,
    )
    return sid


async def _seed_rule(c: Any, *, name: str) -> dict[str, Any]:
    rule_id = _core_id.uuid7()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await c.execute(
        """
        INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
            (id, org_id, name, description, target, dsl, condition, severity_id,
             notify_template_key, labels, is_active, created_at, updated_at)
        VALUES ($1,$2,$3,'','metrics',$4::jsonb,$5::jsonb,2,'alert.test','{}'::jsonb,TRUE,$6,$6)
        """,
        rule_id, _ORG_ID, name,
        json.dumps({
            "target": "metrics", "metric_key": "x.y",
            "timerange": {"last": "5m"}, "aggregate": "sum", "bucket": "1m",
        }),
        json.dumps({"op": "gt", "threshold": 0.0, "for_duration_seconds": 0}),
        now,
    )
    row = await c.fetchrow(
        'SELECT id, org_id, name, notify_template_key, labels, severity_code FROM "05_monitoring"."v_monitoring_alert_rules" WHERE id=$1',
        rule_id,
    )
    return dict(row)


@pytest.mark.asyncio
async def test_silence_matches_by_rule_id(pool):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="sil-rule-id")
        sid = await _seed_silence(c, rule_id=rule["id"])
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        matched = await _service.find_matching_silences(
            c, org_id=_ORG_ID, rule_id=rule["id"], labels={}, now=now,
        )
        assert matched == sid


@pytest.mark.asyncio
async def test_silence_matches_by_labels(pool):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="sil-labels")
        sid = await _seed_silence(c, labels={"team": "platform"})
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        matched = await _service.find_matching_silences(
            c, org_id=_ORG_ID, rule_id=rule["id"],
            labels={"team": "platform", "env": "prod"}, now=now,
        )
        assert matched == sid


@pytest.mark.asyncio
async def test_expired_silence_does_not_match(pool):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="sil-expired")
        await _seed_silence(c, rule_id=rule["id"], expired=True)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        matched = await _service.find_matching_silences(
            c, org_id=_ORG_ID, rule_id=rule["id"], labels={}, now=now,
        )
        assert matched is None


class _FakeTransition:
    def __init__(self, kind: str, fingerprint: str, value: float, threshold: float, labels: dict[str, str]) -> None:
        self.kind = kind
        self.fingerprint = fingerprint
        self.value = value
        self.threshold = threshold
        self.labels = labels


def _make_config() -> Any:
    class _Cfg:
        monitoring_alert_eval_interval_s = 30
        monitoring_alert_notify_throttle_minutes = 15
    return _Cfg()


@pytest.mark.asyncio
async def test_silenced_alert_skips_notify(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="sil-skip")
        # Worker reads rule.labels for recipient — add it.
        await c.execute(
            'UPDATE "05_monitoring"."12_fct_monitoring_alert_rules" SET labels=$1::jsonb WHERE id=$2',
            json.dumps({"recipient_user_id": "user@example.com"}), rule["id"],
        )
        await _seed_silence(c, rule_id=rule["id"])

    # Re-fetch rule with silence-relevant labels.
    async with pool.acquire() as c:
        rule = dict(await c.fetchrow(
            'SELECT id, org_id, name, notify_template_key, labels, severity_code FROM "05_monitoring"."v_monitoring_alert_rules" WHERE id=$1',
            rule["id"],
        ))

    calls: list[dict[str, Any]] = []

    async def _fake_run_node(_pool: Any, key: str, _ctx: Any, inputs: dict) -> dict:
        calls.append({"key": key, "inputs": inputs})
        return {"delivery_id": "x"}

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _fake_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    transition = _FakeTransition("firing_new", "fp-silenced", 10.0, 5.0, {})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await worker._handle_transition(rule, transition, ctx, now)

    # Event inserted with silenced=True
    async with pool.acquire() as c:
        row = await c.fetchrow(
            'SELECT silenced, silence_id FROM "05_monitoring"."60_evt_monitoring_alert_events" '
            'WHERE rule_id=$1 AND fingerprint=$2',
            rule["id"], "fp-silenced",
        )
        assert row is not None
        assert row["silenced"] is True
        assert row["silence_id"] is not None

    # No notify call.
    assert [c for c in calls if c["key"] == "notify.send.transactional"] == []


@pytest.mark.asyncio
async def test_empty_matcher_does_not_match(pool):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="sil-empty")
        # Empty matcher `{}` — per migration comment, matches nothing.
        sid = _core_id.uuid7()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await c.execute(
            """
            INSERT INTO "05_monitoring"."13_fct_monitoring_silences"
                (id, org_id, matcher, starts_at, ends_at, reason, created_by,
                 is_active, created_at, updated_at)
            VALUES ($1,$2,'{}'::jsonb,$3,$4,'empty',$5,TRUE,$6,$6)
            """,
            sid, _ORG_ID, now - timedelta(minutes=1), now + timedelta(hours=1),
            _USER_ID, now,
        )
        matched = await _service.find_matching_silences(
            c, org_id=_ORG_ID, rule_id=rule["id"], labels={"k": "v"}, now=now,
        )
        assert matched is None
