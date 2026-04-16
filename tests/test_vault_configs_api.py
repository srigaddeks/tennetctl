"""
Integration tests for vault.configs — plan 07-03.

Runs against the LIVE tennetctl DB.
Covers: CRUD, typed values, scope coexistence, scope uniqueness, type-mismatch 422.

Configs are plaintext — value IS visible in every response.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")

_PREFIX = "itest-cfg-"


async def _cleanup_config_rows(pool: Any) -> None:
    """Remove all config rows (+ audit + dtl_attrs) created by these tests."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'vault.configs.%'
              AND metadata->>'key' LIKE $1
            """,
            _PREFIX + "%",
        )
        await conn.execute(
            """
            DELETE FROM "02_vault"."21_dtl_attrs"
            WHERE entity_id IN (
                SELECT id FROM "02_vault"."11_fct_vault_configs" WHERE key LIKE $1
            )
            """,
            _PREFIX + "%",
        )
        await conn.execute(
            'DELETE FROM "02_vault"."11_fct_vault_configs" WHERE key LIKE $1',
            _PREFIX + "%",
        )


@pytest.fixture
async def live_app():
    """Boot the FastAPI app against the live DB; yield (client, pool)."""
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup_config_rows(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup_config_rows(pool)
            _catalog.clear_checkers()


async def _count_config_events(pool: Any, event_key: str, key: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT count(*) FROM "04_audit"."60_evt_audit"
            WHERE event_key = $1 AND metadata->>'key' = $2
            """,
            event_key, key,
        )


# ─────────────────────────────────────────────────────────────────────
# Full CRUD round-trip (string type, global scope)
# ─────────────────────────────────────────────────────────────────────

async def test_config_crud_round_trip(live_app) -> None:
    client, pool = live_app
    key = f"{_PREFIX}crud"

    # Create
    resp = await client.post(
        "/v1/vault-configs",
        json={
            "key": key,
            "value_type": "string",
            "value": "hello world",
            "description": "crud test",
            "scope": "global",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ok"] is True
    meta = body["data"]
    config_id = meta["id"]
    assert meta["key"] == key
    assert meta["value_type"] == "string"
    assert meta["value"] == "hello world"
    assert meta["description"] == "crud test"
    assert meta["scope"] == "global"
    assert meta["org_id"] is None
    assert meta["workspace_id"] is None
    assert meta["is_active"] is True
    assert await _count_config_events(pool, "vault.configs.created", key) == 1

    # List — config appears, value visible
    resp = await client.get("/v1/vault-configs")
    assert resp.status_code == 200
    items = resp.json()["data"]
    matching = [c for c in items if c["key"] == key]
    assert len(matching) == 1
    assert matching[0]["value"] == "hello world"

    # Get by ID
    resp = await client.get(f"/v1/vault-configs/{config_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["value"] == "hello world"

    # Update value
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}",
        json={"value": "updated value"},
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()["data"]
    assert updated["value"] == "updated value"
    assert updated["description"] == "crud test"  # description unchanged
    assert await _count_config_events(pool, "vault.configs.updated", key) == 1

    # Get after update
    resp = await client.get(f"/v1/vault-configs/{config_id}")
    assert resp.json()["data"]["value"] == "updated value"

    # Delete
    resp = await client.delete(f"/v1/vault-configs/{config_id}")
    assert resp.status_code == 204

    # 404 after delete
    resp = await client.get(f"/v1/vault-configs/{config_id}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

    # Absent from list
    resp = await client.get("/v1/vault-configs")
    keys_in_list = [c["key"] for c in resp.json()["data"]]
    assert key not in keys_in_list
    assert await _count_config_events(pool, "vault.configs.deleted", key) == 1


# ─────────────────────────────────────────────────────────────────────
# Typed values — boolean
# ─────────────────────────────────────────────────────────────────────

async def test_config_type_boolean(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}bool"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "boolean", "value": True, "scope": "global"},
    )
    assert resp.status_code == 201, resp.text
    meta = resp.json()["data"]
    assert meta["value"] is True
    assert meta["value_type"] == "boolean"

    # Toggle via PATCH
    config_id = meta["id"]
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"value": False}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["value"] is False


# ─────────────────────────────────────────────────────────────────────
# Typed values — number (int + float)
# ─────────────────────────────────────────────────────────────────────

async def test_config_type_number(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}num"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "number", "value": 42, "scope": "global"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["value"] == 42

    # Update to float
    config_id = resp.json()["data"]["id"]
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"value": 3.14}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["value"] == pytest.approx(3.14)


# ─────────────────────────────────────────────────────────────────────
# Typed values — json object
# ─────────────────────────────────────────────────────────────────────

async def test_config_type_json(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}json"
    payload = {"rate": 100, "burst": 20, "enabled": True}

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "json", "value": payload, "scope": "global"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["value"] == payload

    # Update to a different JSON value
    config_id = resp.json()["data"]["id"]
    new_payload = {"rate": 200, "burst": 40}
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"value": new_payload}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["value"] == new_payload


# ─────────────────────────────────────────────────────────────────────
# Type mismatch on CREATE → 422
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("value_type,bad_value", [
    ("boolean", "yes"),         # string is not boolean
    ("boolean", 1),             # int is not boolean
    ("number", "not-a-number"), # string is not number
    ("number", True),           # bool is not number (bool subclasses int but rejected)
])
async def test_config_type_mismatch_create_rejected(
    live_app, value_type: str, bad_value: Any
) -> None:
    client, _pool = live_app
    resp = await client.post(
        "/v1/vault-configs",
        json={
            "key": f"{_PREFIX}tmm",
            "value_type": value_type,
            "value": bad_value,
            "scope": "global",
        },
    )
    assert resp.status_code == 422, (
        f"value_type={value_type!r}, bad_value={bad_value!r} — expected 422, got {resp.status_code}"
    )


# ─────────────────────────────────────────────────────────────────────
# Type mismatch on UPDATE → 422
# ─────────────────────────────────────────────────────────────────────

async def test_config_type_mismatch_update_rejected(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}tmm-update"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "number", "value": 10, "scope": "global"},
    )
    assert resp.status_code == 201
    config_id = resp.json()["data"]["id"]

    # Try patching a number config with a boolean value.
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"value": True}
    )
    assert resp.status_code == 422, f"expected 422, got {resp.status_code}: {resp.text}"


# ─────────────────────────────────────────────────────────────────────
# Scope uniqueness — same key + same scope → 409
# ─────────────────────────────────────────────────────────────────────

async def test_config_scope_uniqueness(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}unique"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "first", "scope": "global"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "second", "scope": "global"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


# ─────────────────────────────────────────────────────────────────────
# Same key at different scopes is allowed
# ─────────────────────────────────────────────────────────────────────

async def test_config_same_key_different_scopes(live_app) -> None:
    client, pool = live_app
    key = f"{_PREFIX}multi-scope"
    fake_org = "00000000-0000-0000-0000-000000000002"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "global-val", "scope": "global"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/v1/vault-configs",
        json={
            "key": key,
            "value_type": "string",
            "value": "org-val",
            "scope": "org",
            "org_id": fake_org,
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["scope"] == "org"
    assert resp.json()["data"]["org_id"] == fake_org

    # Both configs visible in list
    resp = await client.get("/v1/vault-configs")
    matching = [c for c in resp.json()["data"] if c["key"] == key]
    assert len(matching) == 2
    scopes = {c["scope"] for c in matching}
    assert scopes == {"global", "org"}

    # Clean up org-scope row explicitly (cleanup fixture deletes by key prefix which covers both)
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "02_vault"."11_fct_vault_configs" WHERE key = $1 AND org_id = $2',
            key, fake_org,
        )


# ─────────────────────────────────────────────────────────────────────
# Description update and clear
# ─────────────────────────────────────────────────────────────────────

async def test_config_description_update_and_clear(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}desc"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "v", "scope": "global"},
    )
    assert resp.status_code == 201
    config_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["description"] is None

    # Set description
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"description": "my note"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["description"] == "my note"

    # Clear description (explicit empty string)
    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"description": ""}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["description"] is None


# ─────────────────────────────────────────────────────────────────────
# Key shape validation
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_key", [
    "UPPER.key",
    "1leading-digit",
    "_underscore",
    "spa ced",
    "slash/bad",
    "a" * 129,
])
async def test_config_key_shape_rejected(live_app, bad_key: str) -> None:
    client, _pool = live_app
    resp = await client.post(
        "/v1/vault-configs",
        json={"key": bad_key, "value_type": "string", "value": "x", "scope": "global"},
    )
    assert resp.status_code == 422, f"bad_key={bad_key!r} got {resp.status_code}"


# ─────────────────────────────────────────────────────────────────────
# Scope shape validation
# ─────────────────────────────────────────────────────────────────────

async def test_config_scope_shape_validated(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}scope-val"

    # org without org_id → 422
    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "x", "scope": "org"},
    )
    assert resp.status_code == 422

    # workspace without workspace_id → 422
    resp = await client.post(
        "/v1/vault-configs",
        json={
            "key": key, "value_type": "string", "value": "x", "scope": "workspace",
            "org_id": "00000000-0000-0000-0000-000000000003",
        },
    )
    assert resp.status_code == 422

    # global with org_id → 422
    resp = await client.post(
        "/v1/vault-configs",
        json={
            "key": key, "value_type": "string", "value": "x", "scope": "global",
            "org_id": "00000000-0000-0000-0000-000000000003",
        },
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# List scope filter
# ─────────────────────────────────────────────────────────────────────

async def test_config_list_scope_filter(live_app) -> None:
    client, pool = live_app
    key = f"{_PREFIX}filter"
    fake_org = "00000000-0000-0000-0000-000000000004"

    await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "g", "scope": "global"},
    )
    await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "o", "scope": "org",
              "org_id": fake_org},
    )

    # Filter to global only
    resp = await client.get("/v1/vault-configs?scope=global")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert all(c["scope"] == "global" for c in items)

    # Filter to org scope only
    resp = await client.get("/v1/vault-configs?scope=org")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert all(c["scope"] == "org" for c in items)

    # Clean up org-scope row
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "02_vault"."11_fct_vault_configs" WHERE key = $1 AND org_id = $2',
            key, fake_org,
        )


# ─────────────────────────────────────────────────────────────────────
# is_active flag toggle
# ─────────────────────────────────────────────────────────────────────

async def test_config_is_active_toggle(live_app) -> None:
    client, _pool = live_app
    key = f"{_PREFIX}active"

    resp = await client.post(
        "/v1/vault-configs",
        json={"key": key, "value_type": "string", "value": "v", "scope": "global"},
    )
    assert resp.status_code == 201
    config_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["is_active"] is True

    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False

    resp = await client.patch(
        f"/v1/vault-configs/{config_id}", json={"is_active": True}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True
