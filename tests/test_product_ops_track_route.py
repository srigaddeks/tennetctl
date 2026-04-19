"""
HTTP integration test for POST /v1/track + GET /v1/product-events.
Skips when the live DB / vault / module aren't ready.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_db: Any = import_module("backend.01_core.database")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)
TEST_PROJECT_KEY = os.environ.get("TEST_PROJECT_KEY", "pk_test_product_ops")
TEST_ORG_ID = os.environ.get("TEST_ORG_ID", "00000000-0000-0000-0000-000000000001")
TEST_WS_ID = os.environ.get("TEST_WORKSPACE_ID", "00000000-0000-0000-0000-000000000002")

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app_client():
    """ASGI client against the FastAPI app. Skips if product_ops module not enabled."""
    os.environ.setdefault("TENNETCTL_MODULES", "core,iam,audit,vault,product_ops")
    _main = import_module("backend.main")

    pool = await _db.create_pool(LIVE_DSN)
    async with pool.acquire() as conn:
        ok = await conn.fetchval(
            "SELECT to_regclass('\"10_product_ops\".\"60_evt_product_events\"')"
        )
        if not ok:
            await pool.close()
            pytest.skip("10_product_ops schema not applied")

    # Provision project key
    try:
        await _catalog.run_node(
            pool, "vault.secrets.put", _ctx_mod.NodeContext.system(),
            {
                "key": f"product_ops/project_keys/{TEST_PROJECT_KEY}",
                "plaintext": json.dumps({"org_id": TEST_ORG_ID, "workspace_id": TEST_WS_ID}),
            },
        )
    except Exception:
        await pool.close()
        pytest.skip("vault.secrets.put unavailable")

    transport = ASGITransport(app=_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "10_product_ops"."60_evt_product_events" WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        await conn.execute(
            'DELETE FROM "10_product_ops"."10_fct_visitors" WHERE workspace_id = $1',
            TEST_WS_ID,
        )
    await pool.close()


async def test_track_endpoint_accepts_batch(app_client: AsyncClient) -> None:
    body = {
        "project_key": TEST_PROJECT_KEY,
        "events": [
            {
                "kind": "page_view",
                "anonymous_id": "v_route_test_1",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "page_url": "https://example.com/?utm_source=twitter",
            }
        ],
    }
    r = await app_client.post("/v1/track", json=body)
    assert r.status_code == 202, r.text
    data = r.json()
    assert data["ok"] is True
    assert data["data"]["accepted"] == 1


async def test_track_rejects_malformed_payload(app_client: AsyncClient) -> None:
    r = await app_client.post("/v1/track", json={"project_key": "x"})  # missing events
    assert r.status_code == 400
    data = r.json()
    assert data.get("ok") is False or "error" in data


async def test_track_dnt_header_drops_events(app_client: AsyncClient) -> None:
    body = {
        "project_key": TEST_PROJECT_KEY,
        "events": [
            {
                "kind": "page_view",
                "anonymous_id": "v_dnt_test",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
    r = await app_client.post("/v1/track", json=body, headers={"DNT": "1"})
    assert r.status_code == 202
    assert r.json()["data"]["dropped_dnt"] == 1


async def test_get_product_events_workspace_scoped(app_client: AsyncClient) -> None:
    # Ingest an event first
    await app_client.post("/v1/track", json={
        "project_key": TEST_PROJECT_KEY,
        "events": [{
            "kind": "custom",
            "event_name": "test_custom",
            "anonymous_id": "v_list_test",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }],
    })

    r = await app_client.get(f"/v1/product-events?workspace_id={TEST_WS_ID}")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    events = data["data"]["events"]
    assert any(e["event_name"] == "test_custom" for e in events)


async def test_get_product_events_requires_workspace(app_client: AsyncClient) -> None:
    r = await app_client.get("/v1/product-events")
    assert r.status_code == 400
