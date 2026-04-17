"""Tests for monitoring.synthetic — CRUD + runner (13-07)."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_runner_mod: Any = import_module(
    "backend.02_features.05_monitoring.workers.synthetic_runner"
)
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.repository"
)

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0707-0006-7000-0000-000000000001"
_WS_ID = "019e0707-0006-7000-0000-000000000002"
_USER_ID = "019e0707-0006-7000-0000-000000000003"
_SESSION_ID = "019e0707-0006-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."20_dtl_monitoring_synthetic_state" '
            'WHERE check_id IN (SELECT id FROM "05_monitoring"."10_fct_monitoring_synthetic_checks" WHERE org_id=$1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_synthetic_checks" WHERE org_id=$1',
            _ORG_ID,
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
async def test_synthetic_crud(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/synthetic-checks",
        json={
            "name": "httpbin-ok",
            "target_url": "http://httpbin/status/200",
            "interval_seconds": 60,
        },
    )
    assert r.status_code == 201, r.text
    check_id = r.json()["data"]["id"]

    r2 = await client.get("/v1/monitoring/synthetic-checks")
    assert r2.status_code == 200
    items = r2.json()["data"]["items"]
    assert any(c["id"] == check_id for c in items)

    r3 = await client.get(f"/v1/monitoring/synthetic-checks/{check_id}")
    assert r3.status_code == 200
    assert r3.json()["data"]["name"] == "httpbin-ok"

    r4 = await client.patch(
        f"/v1/monitoring/synthetic-checks/{check_id}",
        json={"expected_status": 201},
    )
    assert r4.status_code == 200
    assert r4.json()["data"]["expected_status"] == 201

    r5 = await client.delete(f"/v1/monitoring/synthetic-checks/{check_id}")
    assert r5.status_code == 204

    r6 = await client.get(f"/v1/monitoring/synthetic-checks/{check_id}")
    assert r6.status_code == 404


@pytest.mark.asyncio
async def test_synthetic_duplicate_rejected(live_app):
    client, _pool = live_app
    body = {"name": "dup", "target_url": "http://httpbin/status/200"}
    r1 = await client.post("/v1/monitoring/synthetic-checks", json=body)
    assert r1.status_code == 201
    r2 = await client.post("/v1/monitoring/synthetic-checks", json=body)
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_synthetic_runner_success_path(live_app, monkeypatch):
    """Mock httpx to return 200; verify state updates + counters reset."""
    client, pool = live_app
    r = await client.post(
        "/v1/monitoring/synthetic-checks",
        json={"name": "ok-check", "target_url": "http://example.com/ok",
              "interval_seconds": 30},
    )
    check_id = r.json()["data"]["id"]

    class _Resp:
        status_code = 200
        text = "ok"

    class _Client:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def request(self, *, method, url, headers=None, content=None):
            return _Resp()

    import httpx as _httpx
    monkeypatch.setattr(_httpx, "AsyncClient", _Client)

    runner = _runner_mod.SyntheticRunner(pool)
    async with pool.acquire() as conn:
        check = await _repo.get_by_id(conn, id=check_id)
    await runner._run_single(check)

    async with pool.acquire() as conn:
        state = await conn.fetchrow(
            'SELECT consecutive_failures, last_status_code, last_ok_at '
            'FROM "05_monitoring"."20_dtl_monitoring_synthetic_state" '
            'WHERE check_id=$1',
            check_id,
        )
    assert state is not None
    assert state["consecutive_failures"] == 0
    assert state["last_status_code"] == 200
    assert state["last_ok_at"] is not None


@pytest.mark.asyncio
async def test_synthetic_runner_failure_increments_counter(live_app, monkeypatch):
    client, pool = live_app
    r = await client.post(
        "/v1/monitoring/synthetic-checks",
        json={"name": "fail-check", "target_url": "http://example.com/x",
              "expected_status": 200},
    )
    check_id = r.json()["data"]["id"]

    class _Resp:
        status_code = 500
        text = "err"

    class _Client:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def request(self, *, method, url, headers=None, content=None):
            return _Resp()

    import httpx as _httpx
    monkeypatch.setattr(_httpx, "AsyncClient", _Client)

    runner = _runner_mod.SyntheticRunner(pool)
    async with pool.acquire() as conn:
        check = await _repo.get_by_id(conn, id=check_id)
    # Two failures
    await runner._run_single(check)
    await runner._run_single(check)

    async with pool.acquire() as conn:
        state = await conn.fetchrow(
            'SELECT consecutive_failures FROM "05_monitoring"."20_dtl_monitoring_synthetic_state" '
            'WHERE check_id=$1',
            check_id,
        )
    assert state["consecutive_failures"] == 2


@pytest.mark.asyncio
async def test_synthetic_assertion_body_contains(live_app, monkeypatch):
    client, pool = live_app
    r = await client.post(
        "/v1/monitoring/synthetic-checks",
        json={
            "name": "assert-check",
            "target_url": "http://example.com/",
            "assertions": [{"op": "contains", "field": "body", "value": "EXPECTED_NOT_PRESENT_XYZ"}],
        },
    )
    check_id = r.json()["data"]["id"]

    class _Resp:
        status_code = 200
        text = "status: ok"

    class _Client:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def request(self, *, method, url, headers=None, content=None):
            return _Resp()

    import httpx as _httpx
    monkeypatch.setattr(_httpx, "AsyncClient", _Client)

    runner = _runner_mod.SyntheticRunner(pool)
    async with pool.acquire() as conn:
        check = await _repo.get_by_id(conn, id=check_id)
    await runner._run_single(check)

    async with pool.acquire() as conn:
        state = await conn.fetchrow(
            'SELECT consecutive_failures, last_error FROM "05_monitoring"."20_dtl_monitoring_synthetic_state" '
            'WHERE check_id=$1',
            check_id,
        )
    # status 200 but assertion fails → consecutive_failures incremented
    assert state["consecutive_failures"] >= 1
    assert state["last_error"] is not None
    assert "assertion" in state["last_error"]


@pytest.mark.asyncio
async def test_synthetic_disable_via_patch(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/synthetic-checks",
        json={"name": "disable-check", "target_url": "http://example.com/"},
    )
    check_id = r.json()["data"]["id"]
    r2 = await client.patch(
        f"/v1/monitoring/synthetic-checks/{check_id}",
        json={"is_active": False},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["is_active"] is False
