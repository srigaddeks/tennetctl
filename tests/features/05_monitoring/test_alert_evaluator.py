"""Tests for the alert evaluator (13-08b).

These tests exercise ``evaluate_rule`` against the live test DB using a seed
rule row + a monkey-patched DSL compiler that returns pre-canned observations.
This keeps the evaluator logic (for_duration gating, fingerprint dedup, resolve
detection, state persistence) decoupled from query-DSL correctness which has
its own test coverage in test_query_dsl.py.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import asyncpg
import pytest

_db_mod: Any = import_module("backend.01_core.database")
_evaluator: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.evaluator"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-000b-7000-0000-000000000001"


@pytest.fixture
async def conn():
    c = await asyncpg.connect(LIVE_DSN)
    await _db_mod._init_conn(c)
    try:
        await _cleanup(c)
        yield c
    finally:
        await _cleanup(c)
        await c.close()


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
    name: str = "eval-rule",
    op: str = "gt",
    threshold: float = 1.0,
    for_duration_seconds: int = 0,
    target: str = "metrics",
) -> dict[str, Any]:
    rule_id = _core_id.uuid7()
    # severity_id=2 is 'warn' per seed (migration 049 seeds 1=info,2=warn,3=critical).
    dsl = {
        "target": target,
        "metric_key": "unit.test.metric",
        "timerange": {"last": "5m"},
        "aggregate": "sum",
        "bucket": "1m",
    } if target == "metrics" else {
        "target": "logs",
        "timerange": {"last": "5m"},
        "limit": 100,
    }
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await c.execute(
        """
        INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
            (id, org_id, name, description, target, dsl, condition,
             severity_id, notify_template_key, labels, is_active,
             created_at, updated_at)
        VALUES ($1,$2,$3,'',$4,$5::jsonb,$6::jsonb,2,'alert.test','{}'::jsonb,TRUE,$7,$7)
        """,
        rule_id, _ORG_ID, name, target,
        json.dumps(dsl),
        json.dumps({"op": op, "threshold": threshold,
                    "for_duration_seconds": for_duration_seconds}),
        now,
    )
    row = await c.fetchrow(
        """
        SELECT id, org_id, name, description, target, dsl, condition,
               severity_id, notify_template_key, labels, is_active, paused_until
          FROM "05_monitoring"."v_monitoring_alert_rules"
         WHERE id=$1
        """,
        rule_id,
    )
    return dict(row)


def _ctx() -> Any:
    return _catalog_ctx.NodeContext(
        org_id=_ORG_ID, trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="system",
    )


def _patch_dsl(monkeypatch: Any, metric_rows: list[dict[str, Any]]) -> None:
    """Patch query_dsl.compile/validate to return canned metric rows.

    The evaluator calls validate_metrics_query then compile_metrics_query and
    executes the returned SQL. We short-circuit by returning a SELECT that
    emits our fixed rows via UNION ALL VALUES.
    """
    dsl_mod: Any = import_module("backend.02_features.05_monitoring.query_dsl")

    class _FakeQ:
        pass

    def _fake_validate(_payload: Any) -> Any:
        return _FakeQ()

    def _fake_compile(_q: Any, _ctx: Any) -> tuple[str, list[Any]]:
        if not metric_rows:
            return ("SELECT NULL::timestamp AS bucket_ts, NULL::double precision AS value, NULL::jsonb AS labels WHERE FALSE", [])
        parts = []
        binds: list[Any] = []
        for row in metric_rows:
            binds.append(row["value"])
            binds.append(json.dumps(row.get("labels") or {}))
            parts.append(
                f"SELECT CURRENT_TIMESTAMP AS bucket_ts, ${len(binds) - 1}::double precision AS value, ${len(binds)}::jsonb AS labels"
            )
        sql = " UNION ALL ".join(parts)
        return sql, binds

    monkeypatch.setattr(_evaluator._dsl, "validate_metrics_query", _fake_validate)
    monkeypatch.setattr(_evaluator._dsl, "compile_metrics_query", _fake_compile)


@pytest.mark.asyncio
async def test_breach_no_for_duration_fires_immediately(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=5.0)
    _patch_dsl(monkeypatch, [{"value": 10.0, "labels": {"svc": "api"}}])
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx())
    assert len(transitions) == 1
    assert transitions[0].kind == "firing_new"
    assert transitions[0].value == 10.0
    assert transitions[0].labels == {"svc": "api"}


@pytest.mark.asyncio
async def test_for_duration_gates_first_breach(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=60, threshold=5.0)
    _patch_dsl(monkeypatch, [{"value": 10.0, "labels": {"svc": "api"}}])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx(), now=now)
    assert transitions == []
    # pending_fingerprints populated.
    row = await conn.fetchrow(
        'SELECT pending_fingerprints FROM "05_monitoring"."20_dtl_monitoring_rule_state" WHERE rule_id=$1',
        rule["id"],
    )
    raw = row["pending_fingerprints"]
    pending = raw if isinstance(raw, dict) else json.loads(raw)
    assert len(pending) == 1


@pytest.mark.asyncio
async def test_for_duration_fires_after_elapsed(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=60, threshold=5.0)
    _patch_dsl(monkeypatch, [{"value": 10.0, "labels": {"svc": "api"}}])
    t0 = datetime.now(timezone.utc).replace(tzinfo=None)
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx(), now=t0)
    assert transitions == []
    t1 = t0 + timedelta(seconds=65)
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx(), now=t1)
    assert len(transitions) == 1
    assert transitions[0].kind == "firing_new"


@pytest.mark.asyncio
async def test_resolve_when_condition_clears(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=5.0)
    # Firing cycle.
    _patch_dsl(monkeypatch, [{"value": 10.0, "labels": {"svc": "api"}}])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx(), now=now)
    assert transitions[0].kind == "firing_new"
    # Manually insert a firing event row (simulating what worker would do).
    fp = transitions[0].fingerprint
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
            (id, rule_id, fingerprint, state, value, threshold, org_id, started_at, labels)
        VALUES ($1,$2,$3,'firing',10.0,5.0,$4,$5,'{}'::jsonb)
        """,
        _core_id.uuid7(), rule["id"], fp, _ORG_ID, now,
    )
    # Clearing cycle.
    _patch_dsl(monkeypatch, [{"value": 1.0, "labels": {"svc": "api"}}])
    transitions = await _evaluator.evaluate_rule(
        conn, rule, _ctx(), now=now + timedelta(seconds=30),
    )
    assert any(t.kind == "resolving" and t.fingerprint == fp for t in transitions)


@pytest.mark.asyncio
async def test_fingerprint_dedup_by_labels(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=0.0)
    _patch_dsl(monkeypatch, [
        {"value": 1.0, "labels": {"svc": "api"}},
        {"value": 1.0, "labels": {"svc": "worker"}},
    ])
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx())
    assert len(transitions) == 2
    # Distinct fingerprints.
    fps = {t.fingerprint for t in transitions}
    assert len(fps) == 2


@pytest.mark.asyncio
async def test_logs_target_counts_rows(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=2.0, target="logs")

    class _FakeQ:
        pass

    def _fake_validate(_payload: Any) -> Any:
        return _FakeQ()

    def _fake_compile(_q: Any, _ctx: Any) -> tuple[str, list[Any]]:
        # 3 dummy rows → count=3, > 2 → fires.
        return (
            "SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3",
            [],
        )

    monkeypatch.setattr(_evaluator._dsl, "validate_logs_query", _fake_validate)
    monkeypatch.setattr(_evaluator._dsl, "compile_logs_query", _fake_compile)

    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx())
    assert len(transitions) == 1
    assert transitions[0].kind == "firing_new"
    assert transitions[0].value == 3.0


@pytest.mark.asyncio
async def test_state_row_created_on_first_eval(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=999.0)
    _patch_dsl(monkeypatch, [{"value": 1.0, "labels": {}}])
    row = await conn.fetchrow(
        'SELECT 1 FROM "05_monitoring"."20_dtl_monitoring_rule_state" WHERE rule_id=$1',
        rule["id"],
    )
    assert row is None
    await _evaluator.evaluate_rule(conn, rule, _ctx())
    row = await conn.fetchrow(
        'SELECT last_eval_at FROM "05_monitoring"."20_dtl_monitoring_rule_state" WHERE rule_id=$1',
        rule["id"],
    )
    assert row is not None
    assert row["last_eval_at"] is not None


@pytest.mark.asyncio
async def test_no_breach_returns_empty(conn, monkeypatch):
    rule = await _seed_rule(conn, for_duration_seconds=0, threshold=100.0)
    _patch_dsl(monkeypatch, [{"value": 1.0, "labels": {}}])
    transitions = await _evaluator.evaluate_rule(conn, rule, _ctx())
    assert transitions == []


@pytest.mark.asyncio
async def test_fingerprint_deterministic():
    f1 = _evaluator.fingerprint_for("rule-A", {"svc": "api", "env": "prod"})
    f2 = _evaluator.fingerprint_for("rule-A", {"env": "prod", "svc": "api"})
    f3 = _evaluator.fingerprint_for("rule-B", {"svc": "api", "env": "prod"})
    assert f1 == f2  # order-independent
    assert f1 != f3  # rule_id mixed in
