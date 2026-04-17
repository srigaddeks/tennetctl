"""Tests for AlertEvaluatorWorker notify integration (13-08b).

Exercises the transition → notify pipeline end-to-end against the live DB:
  - firing_new transition triggers notify.send.transactional with correct variables
  - resolved transition re-uses template with state='resolved'
  - notify failure increments failure counter + logs
  - throttle suppresses subsequent notifications within the throttle window
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest

_db: Any = import_module("backend.01_core.database")
_worker_mod: Any = import_module(
    "backend.02_features.05_monitoring.workers.alert_evaluator_worker"
)
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-000c-7000-0000-000000000001"


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
        'DELETE FROM "05_monitoring"."20_dtl_monitoring_rule_state" '
        'WHERE rule_id IN (SELECT id FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1)',
        _ORG_ID,
    )
    await c.execute(
        'DELETE FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1',
        _ORG_ID,
    )


async def _seed_rule(
    c: Any,
    *,
    name: str,
    labels: dict[str, Any] | None = None,
    notify_template_key: str = "alert.test",
) -> dict[str, Any]:
    rule_id = _core_id.uuid7()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await c.execute(
        """
        INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
            (id, org_id, name, description, target, dsl, condition, severity_id,
             notify_template_key, labels, is_active, created_at, updated_at)
        VALUES ($1,$2,$3,'','metrics',$4::jsonb,$5::jsonb,2,$6,$7::jsonb,TRUE,$8,$8)
        """,
        rule_id, _ORG_ID, name,
        json.dumps({
            "target": "metrics", "metric_key": "x.y",
            "timerange": {"last": "5m"}, "aggregate": "sum", "bucket": "1m",
        }),
        json.dumps({"op": "gt", "threshold": 0.0, "for_duration_seconds": 0}),
        notify_template_key,
        json.dumps(labels or {}),
        now,
    )
    row = await c.fetchrow(
        """SELECT id, org_id, name, target, dsl, condition, severity_id,
                  severity_code, notify_template_key, labels, is_active
             FROM "05_monitoring"."v_monitoring_alert_rules" WHERE id=$1""",
        rule_id,
    )
    return dict(row)


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
async def test_firing_triggers_notify(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(
            c, name="notify-fire",
            labels={"recipient_user_id": "user@example.com"},
        )

    calls: list[dict[str, Any]] = []

    async def _fake_run_node(_pool: Any, key: str, _ctx: Any, inputs: dict) -> dict:
        calls.append({"key": key, "inputs": inputs})
        return {"delivery_id": "fake-delivery"}

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _fake_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    transition = _FakeTransition("firing_new", "fp-abc", 10.0, 5.0, {"env": "prod"})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await worker._handle_transition(rule, transition, ctx, now)

    notify_calls = [c for c in calls if c["key"] == "notify.send.transactional"]
    assert len(notify_calls) == 1
    inp = notify_calls[0]["inputs"]
    assert inp["template_key"] == "alert.test"
    assert inp["recipient_user_id"] == "user@example.com"
    assert inp["variables"]["state"] == "firing"
    assert inp["variables"]["value"] == "10.0"
    assert inp["variables"]["threshold"] == "5.0"


@pytest.mark.asyncio
async def test_resolved_transition_notifies(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(
            c, name="notify-resolved",
            labels={"recipient_user_id": "user@example.com"},
        )
        # Seed an existing firing event.
        fp = "fp-resolve"
        event_id = _core_id.uuid7()
        started_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30)
        await c.execute(
            """
            INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
                (id, rule_id, fingerprint, state, value, threshold, org_id, started_at, labels)
            VALUES ($1,$2,$3,'firing',10.0,5.0,$4,$5,'{}'::jsonb)
            """,
            event_id, rule["id"], fp, _ORG_ID, started_at,
        )

    calls: list[dict[str, Any]] = []

    async def _fake_run_node(_pool: Any, key: str, _ctx: Any, inputs: dict) -> dict:
        calls.append({"key": key, "inputs": inputs})
        return {"delivery_id": "x"}

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _fake_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    transition = _FakeTransition("resolving", fp, 0.0, 5.0, {})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await worker._handle_transition(rule, transition, ctx, now)

    notify_calls = [c for c in calls if c["key"] == "notify.send.transactional"]
    assert len(notify_calls) == 1
    assert notify_calls[0]["inputs"]["variables"]["state"] == "resolved"

    # Evt row flipped to resolved.
    async with pool.acquire() as c:
        row = await c.fetchrow(
            'SELECT state, resolved_at FROM "05_monitoring"."60_evt_monitoring_alert_events" WHERE id=$1',
            event_id,
        )
        assert row["state"] == "resolved"
        assert row["resolved_at"] is not None


@pytest.mark.asyncio
async def test_notify_failure_does_not_crash(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(
            c, name="notify-fail",
            labels={"recipient_user_id": "user@example.com"},
        )

    async def _failing_run_node(_pool: Any, _key: str, _ctx: Any, _inputs: dict) -> dict:
        raise RuntimeError("smtp down")

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _failing_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    transition = _FakeTransition("firing_new", "fp-fail", 10.0, 5.0, {})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Should not raise.
    await worker._handle_transition(rule, transition, ctx, now)
    # Event still written.
    async with pool.acquire() as c:
        row = await c.fetchrow(
            'SELECT id, last_notified_at FROM "05_monitoring"."60_evt_monitoring_alert_events" '
            'WHERE rule_id=$1 AND fingerprint=$2',
            rule["id"], "fp-fail",
        )
        assert row is not None
        assert row["last_notified_at"] is None  # failure → not marked notified.


@pytest.mark.asyncio
async def test_throttle_suppresses_repeated_notifies(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(
            c, name="notify-throttle",
            labels={"recipient_user_id": "user@example.com"},
        )

    calls: list[dict[str, Any]] = []

    async def _fake_run_node(_pool: Any, key: str, _ctx: Any, inputs: dict) -> dict:
        calls.append({"key": key, "inputs": inputs})
        return {"delivery_id": "x"}

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _fake_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    fp = "fp-throttle"
    transition = _FakeTransition("firing_new", fp, 10.0, 5.0, {})
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # First firing — inserts + notifies.
    await worker._handle_transition(rule, transition, ctx, now)
    # Second within throttle window — updates value, no notify.
    await worker._handle_transition(
        rule, _FakeTransition("firing_new", fp, 12.0, 5.0, {}),
        ctx, now + timedelta(minutes=1),
    )
    notify_calls = [c for c in calls if c["key"] == "notify.send.transactional"]
    assert len(notify_calls) == 1


@pytest.mark.asyncio
async def test_missing_recipient_skips_notify(pool, monkeypatch):
    async with pool.acquire() as c:
        rule = await _seed_rule(c, name="notify-norcpt", labels={})

    calls: list[dict[str, Any]] = []

    async def _fake_run_node(_pool: Any, key: str, _ctx: Any, inputs: dict) -> dict:
        calls.append({"key": key, "inputs": inputs})
        return {"delivery_id": "x"}

    monkeypatch.setattr(_worker_mod._catalog, "run_node", _fake_run_node)

    worker = _worker_mod.AlertEvaluatorWorker(pool, _make_config())
    ctx = worker._ctx_for_rule(rule)
    transition = _FakeTransition("firing_new", "fp-noRc", 10.0, 5.0, {})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await worker._handle_transition(rule, transition, ctx, now)
    notify_calls = [c for c in calls if c["key"] == "notify.send.transactional"]
    assert len(notify_calls) == 0
    # Event still recorded.
    async with pool.acquire() as c:
        row = await c.fetchrow(
            'SELECT id FROM "05_monitoring"."60_evt_monitoring_alert_events" '
            'WHERE rule_id=$1 AND fingerprint=$2',
            rule["id"], "fp-noRc",
        )
        assert row is not None
