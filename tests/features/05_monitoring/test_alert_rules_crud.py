"""Tests for monitoring.alerts — rule CRUD (13-08a chunk A)."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-0007-7000-0000-000000000001"
_WS_ID = "019e0808-0007-7000-0000-000000000002"
_USER_ID = "019e0808-0007-7000-0000-000000000003"
_SESSION_ID = "019e0808-0007-7000-0000-000000000004"
_OTHER_ORG = "019e0808-0007-7000-0000-0000000000aa"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}
_HDR_OTHER = {
    "x-org-id": _OTHER_ORG, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


def _valid_dsl() -> dict[str, Any]:
    return {
        "target": "metrics",
        "metric_key": "alert.test.counter",
        "timerange": {"last": "15m"},
        "aggregate": "sum",
        "bucket": "1m",
    }


def _valid_create_body(name: str = "test-rule") -> dict[str, Any]:
    return {
        "name": name,
        "description": "unit-test rule",
        "target": "metrics",
        "dsl": _valid_dsl(),
        "condition": {"op": "gt", "threshold": 0.0, "for_duration_seconds": 0},
        "severity": "warn",
        "notify_template_key": "test.alert",
        "labels": {"team": "platform"},
    }


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        for org in (_ORG_ID, _OTHER_ORG):
            await conn.execute(
                'DELETE FROM "05_monitoring"."20_dtl_monitoring_rule_state" '
                'WHERE rule_id IN (SELECT id FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1)',
                org,
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE org_id=$1',
                org,
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."13_fct_monitoring_silences" WHERE org_id=$1',
                org,
            )


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
async def test_create_rule_happy_path(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("alpha"),
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["name"] == "alpha"
    assert data["severity"] == "warn"
    assert data["severity_label"] == "Warn"
    assert data["target"] == "metrics"
    assert data["is_active"] is True
    assert data["condition"]["op"] == "gt"
    assert data["labels"] == {"team": "platform"}
    assert "id" in data


@pytest.mark.asyncio
async def test_create_rule_invalid_dsl(live_app):
    client, _pool = live_app
    body = _valid_create_body("bad-dsl")
    body["dsl"] = {"target": "metrics"}  # missing required fields
    r = await client.post("/v1/monitoring/alert-rules", json=body)
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "INVALID_DSL"


@pytest.mark.asyncio
async def test_create_rule_invalid_severity(live_app):
    client, _pool = live_app
    body = _valid_create_body("bad-sev")
    body["severity"] = "extreme"
    r = await client.post("/v1/monitoring/alert-rules", json=body)
    # Pydantic Literal validation rejects unknown values with 422.
    assert r.status_code in (400, 422), r.text


@pytest.mark.asyncio
async def test_create_rule_invalid_target(live_app):
    client, _pool = live_app
    body = _valid_create_body("bad-target")
    body["target"] = "traces"
    r = await client.post("/v1/monitoring/alert-rules", json=body)
    assert r.status_code in (400, 422), r.text


@pytest.mark.asyncio
async def test_create_rule_duplicate_name_rejected(live_app):
    client, _pool = live_app
    body = _valid_create_body("dup")
    r1 = await client.post("/v1/monitoring/alert-rules", json=body)
    assert r1.status_code == 201
    r2 = await client.post("/v1/monitoring/alert-rules", json=body)
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "DUPLICATE"


@pytest.mark.asyncio
async def test_list_rules_returns_created(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("listed"),
    )
    rid = r.json()["data"]["id"]

    rl = await client.get("/v1/monitoring/alert-rules")
    assert rl.status_code == 200
    items = rl.json()["data"]["items"]
    assert any(i["id"] == rid for i in items)

    # Active filter
    rl2 = await client.get("/v1/monitoring/alert-rules?is_active=true")
    assert rl2.status_code == 200
    assert any(i["id"] == rid for i in rl2.json()["data"]["items"])


@pytest.mark.asyncio
async def test_get_rule_by_id(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("get-one"),
    )
    rid = r.json()["data"]["id"]

    rg = await client.get(f"/v1/monitoring/alert-rules/{rid}")
    assert rg.status_code == 200
    assert rg.json()["data"]["name"] == "get-one"


@pytest.mark.asyncio
async def test_update_rule_pause_unpause_and_condition(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("mut-rule"),
    )
    rid = r.json()["data"]["id"]

    # Update condition
    r2 = await client.patch(
        f"/v1/monitoring/alert-rules/{rid}",
        json={
            "condition": {"op": "gte", "threshold": 10, "for_duration_seconds": 60},
            "description": "changed",
        },
    )
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["condition"]["op"] == "gte"
    assert data["condition"]["threshold"] == 10
    assert data["description"] == "changed"

    # Pause
    r3 = await client.post(
        f"/v1/monitoring/alert-rules/{rid}/pause",
        json={"paused_until": "2099-01-01T00:00:00Z"},
    )
    assert r3.status_code == 200
    assert r3.json()["data"]["paused_until"] is not None

    # Unpause
    r4 = await client.post(f"/v1/monitoring/alert-rules/{rid}/unpause")
    assert r4.status_code == 200
    assert r4.json()["data"]["paused_until"] is None


@pytest.mark.asyncio
async def test_soft_delete_removes_from_list(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("del-me"),
    )
    rid = r.json()["data"]["id"]

    rd = await client.delete(f"/v1/monitoring/alert-rules/{rid}")
    assert rd.status_code == 204

    rg = await client.get(f"/v1/monitoring/alert-rules/{rid}")
    assert rg.status_code == 404

    rl = await client.get("/v1/monitoring/alert-rules")
    assert not any(i["id"] == rid for i in rl.json()["data"]["items"])


@pytest.mark.asyncio
async def test_cross_org_read_returns_404(live_app):
    client, pool = live_app
    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("org-iso"),
    )
    rid = r.json()["data"]["id"]

    transport = ASGITransport(app=_main.app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=_HDR_OTHER,
    ) as other:
        rg = await other.get(f"/v1/monitoring/alert-rules/{rid}")
        assert rg.status_code == 404


@pytest.mark.asyncio
async def test_audit_event_emitted_on_create(live_app, monkeypatch):
    """Verify run_node('audit.events.emit', ...) is called on mutations."""
    client, _pool = live_app
    calls: list[tuple[str, dict[str, Any]]] = []

    _catalog_mod: Any = import_module("backend.01_catalog")
    original = _catalog_mod.run_node

    async def _capture(pool: Any, key: str, ctx: Any, inputs: Any) -> Any:
        if key == "audit.events.emit":
            calls.append((key, dict(inputs)))
            return {"ok": True}
        return await original(pool, key, ctx, inputs)

    monkeypatch.setattr(_catalog_mod, "run_node", _capture)
    # Patch the service-level reference too (service imports _catalog at module
    # load; monkeypatching the package attr is not enough).
    _service: Any = import_module(
        "backend.02_features.05_monitoring.sub_features.07_alerts.service"
    )
    monkeypatch.setattr(_service._catalog, "run_node", _capture)

    r = await client.post(
        "/v1/monitoring/alert-rules", json=_valid_create_body("audited"),
    )
    assert r.status_code == 201
    rid = r.json()["data"]["id"]

    r2 = await client.patch(
        f"/v1/monitoring/alert-rules/{rid}", json={"description": "bump"},
    )
    assert r2.status_code == 200

    r3 = await client.delete(f"/v1/monitoring/alert-rules/{rid}")
    assert r3.status_code == 204

    keys = [c[1].get("event_key") for c in calls]
    assert "monitoring.alerts.rule_created" in keys
    assert "monitoring.alerts.rule_updated" in keys
    assert "monitoring.alerts.rule_deleted" in keys
