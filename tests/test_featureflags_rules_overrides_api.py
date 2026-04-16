"""Integration tests for featureflags.rules + featureflags.overrides."""
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

_FLAG_PREFIX = "itest_ffro_"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        flag_rows = await conn.fetch(
            'SELECT id FROM "09_featureflags"."10_fct_flags" WHERE flag_key LIKE $1',
            f"{_FLAG_PREFIX}%",
        )
        flag_ids = [r["id"] for r in flag_rows]
        if not flag_ids:
            return
        await conn.execute(
            'DELETE FROM "09_featureflags"."21_fct_overrides" WHERE flag_id = ANY($1::text[])',
            flag_ids,
        )
        await conn.execute(
            'DELETE FROM "09_featureflags"."20_fct_rules" WHERE flag_id = ANY($1::text[])',
            flag_ids,
        )
        await conn.execute(
            "DELETE FROM \"04_audit\".\"60_evt_audit\" "
            "WHERE event_key LIKE 'featureflags.%' AND metadata->>'flag_id' = ANY($1::text[])",
            flag_ids,
        )
        await conn.execute(
            'DELETE FROM "09_featureflags"."11_fct_flag_states" WHERE flag_id = ANY($1::text[])',
            flag_ids,
        )
        await conn.execute(
            'DELETE FROM "09_featureflags"."10_fct_flags" WHERE id = ANY($1::text[])',
            flag_ids,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


async def _make_flag(client: AsyncClient, key: str) -> str:
    r = await client.post(
        "/v1/flags",
        json={"scope": "global", "flag_key": key, "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.mark.asyncio
async def test_rule_crud(live_app) -> None:
    client, _pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}rule_test")

    r = await client.post(
        "/v1/flag-rules",
        json={
            "flag_id": flag_id,
            "environment": "prod",
            "priority": 10,
            "conditions": {"op": "eq", "attr": "country", "value": "US"},
            "value": True,
            "rollout_percentage": 50,
        },
    )
    assert r.status_code == 201, r.text
    rule = r.json()["data"]
    assert rule["environment"] == "prod"
    assert rule["rollout_percentage"] == 50

    r = await client.get(f"/v1/flag-rules?flag_id={flag_id}&environment=prod")
    assert r.status_code == 200
    assert any(x["id"] == rule["id"] for x in r.json()["data"])

    r = await client.patch(
        f"/v1/flag-rules/{rule['id']}",
        json={"rollout_percentage": 75},
    )
    assert r.status_code == 200
    assert r.json()["data"]["rollout_percentage"] == 75

    r = await client.delete(f"/v1/flag-rules/{rule['id']}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_override_crud(live_app) -> None:
    client, _pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}override_test")

    r = await client.post(
        "/v1/flag-overrides",
        json={
            "flag_id": flag_id,
            "environment": "dev",
            "entity_type": "user",
            "entity_id": "00000000-0000-0000-0000-000000000099",
            "value": True,
            "reason": "QA testing",
        },
    )
    assert r.status_code == 201, r.text
    ov = r.json()["data"]
    assert ov["entity_type"] == "user"
    assert ov["reason"] == "QA testing"

    # Duplicate key → 409
    r = await client.post(
        "/v1/flag-overrides",
        json={
            "flag_id": flag_id,
            "environment": "dev",
            "entity_type": "user",
            "entity_id": "00000000-0000-0000-0000-000000000099",
            "value": False,
        },
    )
    assert r.status_code == 409

    r = await client.get(f"/v1/flag-overrides?flag_id={flag_id}")
    assert len(r.json()["data"]) == 1

    r = await client.patch(
        f"/v1/flag-overrides/{ov['id']}",
        json={"value": False, "reason": "Flipped for QA"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["value"] is False

    r = await client.delete(f"/v1/flag-overrides/{ov['id']}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_rule_rejects_missing_flag(live_app) -> None:
    client, _pool = live_app
    r = await client.post(
        "/v1/flag-rules",
        json={
            "flag_id": "00000000-0000-0000-0000-000000000000",
            "environment": "prod",
            "priority": 1,
            "conditions": {"op": "eq", "attr": "x", "value": "y"},
            "value": True,
        },
    )
    assert r.status_code == 404
