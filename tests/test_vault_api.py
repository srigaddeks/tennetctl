"""
Integration tests for vault.secrets — plan 07-01/07-03 AC.

Runs against the LIVE tennetctl DB (pattern mirrors test_iam_orgs_api.py).
Each test cleans up its rows in setup + teardown.

Plan 07-03 notes:
  - scope='global' required in all create bodies (no longer optional in practice)
  - GET /v1/vault/{key} removed — no HTTP plaintext view after reveal-once
  - vault.secrets.read audit event removed (no HTTP read path)
  - Rotate + delete take ?scope=global (default in routes; explicit here for clarity)

Reverse-search guards:
  - test_plaintext_never_logged    — caplog grep for the sentinel
  - test_ciphertext_is_binary      — DB scan confirms plaintext isn't stored
  - test_list_has_no_value         — HTTP list response never carries value
"""

from __future__ import annotations

import asyncio
import logging
import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_client_mod: Any = import_module("backend.02_features.02_vault.client")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_PREFIX = "itest-vault-"


async def _cleanup_test_rows(pool: Any) -> None:
    """Remove all rows created by these tests — runs in setup + teardown."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'vault.secrets.%'
              AND metadata->>'key' LIKE $1
            """,
            _PREFIX + "%",
        )
        await conn.execute(
            """
            DELETE FROM "02_vault"."21_dtl_attrs"
            WHERE entity_id IN (
                SELECT id FROM "02_vault"."10_fct_vault_entries" WHERE key LIKE $1
            )
            """,
            _PREFIX + "%",
        )
        await conn.execute(
            'DELETE FROM "02_vault"."10_fct_vault_entries" WHERE key LIKE $1',
            _PREFIX + "%",
        )


@pytest.fixture
async def live_app():
    """Boot the FastAPI app against the live DB; yield (client, pool, vault)."""
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault
        await _cleanup_test_rows(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool, vault
        finally:
            await _cleanup_test_rows(pool)
            _catalog.clear_checkers()


async def _count_events(pool: Any, event_key: str, key: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT count(*) FROM "04_audit"."60_evt_audit"
            WHERE event_key = $1 AND metadata->>'key' = $2
            """,
            event_key, key,
        )


async def _fetch_row(pool: Any, key: str) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, key, version, ciphertext, deleted_at "
            'FROM "02_vault"."10_fct_vault_entries" '
            "WHERE key = $1 ORDER BY version",
            key,
        )
        return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# AC-3: CRUD via HTTP — scope-aware, metadata-only responses
# ─────────────────────────────────────────────────────────────────────

async def test_crud_round_trip(live_app) -> None:
    client, _pool, _vault = live_app
    key = f"{_PREFIX}crud"

    # Create — must carry scope; returns metadata only (no value / ciphertext).
    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "hunter2", "description": "crud test", "scope": "global"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ok"] is True
    meta = body["data"]
    assert meta["key"] == key
    assert meta["version"] == 1
    assert meta["description"] == "crud test"
    assert meta["scope"] == "global"
    assert meta["org_id"] is None
    assert meta["workspace_id"] is None
    for forbidden in ("value", "ciphertext", "wrapped_dek", "nonce"):
        assert forbidden not in meta

    # List — metadata only; no forbidden fields on any row.
    resp = await client.get("/v1/vault")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    for item in payload["data"]:
        for forbidden in ("value", "ciphertext", "wrapped_dek", "nonce"):
            assert forbidden not in item

    # Rotate — bumps version; still metadata only.
    resp = await client.post(
        f"/v1/vault/{key}/rotate",
        params={"scope": "global"},
        json={"value": "hunter3"},
    )
    assert resp.status_code == 200, resp.text
    rotated = resp.json()["data"]
    assert rotated["version"] == 2
    assert rotated["scope"] == "global"
    for forbidden in ("value", "ciphertext"):
        assert forbidden not in rotated

    # Delete — 204, no body.
    resp = await client.delete(f"/v1/vault/{key}", params={"scope": "global"})
    assert resp.status_code == 204

    # Deleted key absent from list.
    resp = await client.get("/v1/vault")
    assert resp.status_code == 200
    keys_in_list = [item["key"] for item in resp.json()["data"]]
    assert key not in keys_in_list


# ─────────────────────────────────────────────────────────────────────
# AC-3 audit emission (vault.secrets.read removed — no HTTP read path)
# ─────────────────────────────────────────────────────────────────────

async def test_audit_events_emitted(live_app) -> None:
    client, pool, _vault = live_app
    key = f"{_PREFIX}audit"

    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "x", "description": "audit", "scope": "global"},
    )
    assert resp.status_code == 201
    assert await _count_events(pool, "vault.secrets.created", key) == 1

    # No HTTP read path after creation — vault.secrets.read is never emitted.

    resp = await client.post(
        f"/v1/vault/{key}/rotate",
        params={"scope": "global"},
        json={"value": "y"},
    )
    assert resp.status_code == 200
    assert await _count_events(pool, "vault.secrets.rotated", key) == 1

    resp = await client.delete(f"/v1/vault/{key}", params={"scope": "global"})
    assert resp.status_code == 204
    assert await _count_events(pool, "vault.secrets.deleted", key) == 1


# ─────────────────────────────────────────────────────────────────────
# AC-3 / AC-4 — deleted key absent from vault client; cache busted
# ─────────────────────────────────────────────────────────────────────

async def test_cannot_read_deleted(live_app) -> None:
    client, _pool, vault = live_app
    key = f"{_PREFIX}del"

    await client.post(
        "/v1/vault", json={"key": key, "value": "gone", "scope": "global"}
    )
    # Warm the cache via in-process client (resolves global scope only).
    assert await vault.get(key) == "gone"

    await client.delete(f"/v1/vault/{key}", params={"scope": "global"})
    # Service invalidates cache; next get raises.
    with pytest.raises(_client_mod.VaultSecretNotFound):
        await vault.get(key)


# ─────────────────────────────────────────────────────────────────────
# AC-3 key recycling refused in v0.2
# ─────────────────────────────────────────────────────────────────────

async def test_key_recycling_refused(live_app) -> None:
    client, _pool, _vault = live_app
    key = f"{_PREFIX}recycle"

    resp = await client.post(
        "/v1/vault", json={"key": key, "value": "first", "scope": "global"}
    )
    assert resp.status_code == 201

    await client.delete(f"/v1/vault/{key}", params={"scope": "global"})

    resp = await client.post(
        "/v1/vault", json={"key": key, "value": "second", "scope": "global"}
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


# ─────────────────────────────────────────────────────────────────────
# AC-3 scope coexistence — same key may exist at different scopes
# ─────────────────────────────────────────────────────────────────────

async def test_same_key_different_scopes(live_app) -> None:
    """global + org scope can coexist for the same key."""
    client, pool, _vault = live_app
    key = f"{_PREFIX}scoped"
    fake_org = "00000000-0000-0000-0000-000000000001"

    resp = await client.post(
        "/v1/vault", json={"key": key, "value": "global-val", "scope": "global"}
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "org-val", "scope": "org", "org_id": fake_org},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["scope"] == "org"

    # Clean up org-scope row (cleanup fixture handles global by key prefix, org-scope too)
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "02_vault"."10_fct_vault_entries" WHERE key = $1 AND org_id = $2',
            key, fake_org,
        )


# ─────────────────────────────────────────────────────────────────────
# AC-6 key shape validation
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_key", [
    "UPPER.key",
    "1leading-digit",
    "_underscore",
    "spa ced",
    "slash/bad",
    "a" * 129,
])
async def test_key_shape_rejected(live_app, bad_key: str) -> None:
    client, _pool, _vault = live_app
    resp = await client.post(
        "/v1/vault", json={"key": bad_key, "value": "x", "scope": "global"}
    )
    assert resp.status_code == 422, f"bad_key={bad_key!r} got {resp.status_code}"


# ─────────────────────────────────────────────────────────────────────
# AC-3 empty value
# ─────────────────────────────────────────────────────────────────────

async def test_empty_value_rejected(live_app) -> None:
    client, _pool, _vault = live_app
    resp = await client.post(
        "/v1/vault",
        json={"key": f"{_PREFIX}empty", "value": "", "scope": "global"},
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# AC-3 scope shape validation
# ─────────────────────────────────────────────────────────────────────

async def test_scope_shape_validated(live_app) -> None:
    client, _pool, _vault = live_app
    key = f"{_PREFIX}scope-shape"

    # org scope without org_id → 422
    resp = await client.post(
        "/v1/vault", json={"key": key, "value": "x", "scope": "org"}
    )
    assert resp.status_code == 422

    # workspace scope without workspace_id → 422
    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "x", "scope": "workspace",
              "org_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert resp.status_code == 422

    # global scope with org_id → 422
    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "x", "scope": "global",
              "org_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# AC-5 run_node for put/get/rotate/delete
# ─────────────────────────────────────────────────────────────────────

async def test_nodes_via_runner(live_app) -> None:
    _client, pool, vault = live_app
    key = f"{_PREFIX}nodes"

    # put (effect, tx=caller) — global scope
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = _ctx_mod.NodeContext(
                audit_category="setup",
                trace_id="t-vn-1", span_id="s-vn-1",
                conn=conn,
                extras={"pool": pool, "vault": vault},
            )
            result = await _catalog.run_node(
                pool, "vault.secrets.put", ctx,
                {"key": key, "value": "node-v1", "description": "via node", "scope": "global"},
            )
    assert "secret" in result and result["secret"]["key"] == key
    assert result["secret"]["version"] == 1
    assert result["secret"]["scope"] == "global"
    assert await _count_events(pool, "vault.secrets.created", key) == 1

    # get (request, no tx) — resolves global scope via VaultClient
    ctx = _ctx_mod.NodeContext(
        audit_category="system",
        trace_id="t-vn-2", span_id="s-vn-2",
        extras={"vault": vault},
    )
    got = await _catalog.run_node(pool, "vault.secrets.get", ctx, {"key": key})
    assert got == {"value": "node-v1", "version": 1}
    assert await _count_events(pool, "vault.secrets.get", key) == 0

    # rotate (effect, tx=caller)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = _ctx_mod.NodeContext(
                audit_category="setup",
                trace_id="t-vn-3", span_id="s-vn-3",
                conn=conn,
                extras={"pool": pool, "vault": vault},
            )
            result = await _catalog.run_node(
                pool, "vault.secrets.rotate", ctx,
                {"key": key, "value": "node-v2", "scope": "global"},
            )
    assert result["secret"]["version"] == 2
    assert await _count_events(pool, "vault.secrets.rotated", key) == 1

    # delete (effect, tx=caller)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = _ctx_mod.NodeContext(
                audit_category="setup",
                trace_id="t-vn-4", span_id="s-vn-4",
                conn=conn,
                extras={"pool": pool, "vault": vault},
            )
            await _catalog.run_node(
                pool, "vault.secrets.delete", ctx,
                {"key": key, "scope": "global"},
            )
    assert await _count_events(pool, "vault.secrets.deleted", key) == 1


# ─────────────────────────────────────────────────────────────────────
# AC-8 plaintext never logged
# ─────────────────────────────────────────────────────────────────────

async def test_plaintext_never_logged(live_app, caplog) -> None:
    client, _pool, _vault = live_app
    sentinel = "sentinel-NEVER-LOG-42"
    key = f"{_PREFIX}logging"

    caplog.set_level(logging.DEBUG)
    await client.post(
        "/v1/vault",
        json={"key": key, "value": sentinel, "description": "log check", "scope": "global"},
    )
    # No GET /{key} — plaintext is never re-fetched over HTTP.
    await client.post(
        f"/v1/vault/{key}/rotate",
        params={"scope": "global"},
        json={"value": sentinel + "-b"},
    )
    await client.delete(f"/v1/vault/{key}", params={"scope": "global"})

    for rec in caplog.records:
        text = rec.getMessage()
        assert sentinel not in text, (
            f"plaintext leaked into log: {rec.levelname} {rec.name}: {text!r}"
        )


# ─────────────────────────────────────────────────────────────────────
# AC-8 ciphertext at rest is binary (not the plaintext)
# ─────────────────────────────────────────────────────────────────────

async def test_ciphertext_is_binary(live_app) -> None:
    client, pool, _vault = live_app
    sentinel = "UNIQUE-SENTINEL-AT-REST-99"
    key = f"{_PREFIX}atrest"

    await client.post(
        "/v1/vault", json={"key": key, "value": sentinel, "scope": "global"}
    )
    rows = await _fetch_row(pool, key)
    assert len(rows) == 1
    ct = bytes(rows[0]["ciphertext"])
    assert sentinel.encode("utf-8") not in ct
    # Ciphertext = plaintext + 16-byte GCM auth tag.
    assert len(ct) == len(sentinel) + 16


# ─────────────────────────────────────────────────────────────────────
# AC-4 cache refresh on rotate
# ─────────────────────────────────────────────────────────────────────

async def test_cache_refresh_on_rotate(live_app) -> None:
    client, _pool, vault = live_app
    key = f"{_PREFIX}cache"

    await client.post(
        "/v1/vault", json={"key": key, "value": "v1", "scope": "global"}
    )
    assert await vault.get(key) == "v1"
    before = vault._fetch_count

    # Second call within TTL — no DB hit.
    assert await vault.get(key) == "v1"
    assert vault._fetch_count == before

    # Rotate via HTTP — service invalidates cache.
    await client.post(
        f"/v1/vault/{key}/rotate",
        params={"scope": "global"},
        json={"value": "v2"},
    )
    assert await vault.get(key) == "v2"
    assert vault._fetch_count == before + 1


# ─────────────────────────────────────────────────────────────────────
# AC-4 cache TTL expiry
# ─────────────────────────────────────────────────────────────────────

async def test_cache_ttl_expiry(live_app) -> None:
    client, pool, _vault = live_app
    key = f"{_PREFIX}ttl"

    await client.post(
        "/v1/vault", json={"key": key, "value": "ttl-v1", "scope": "global"}
    )

    _vault_client_mod = import_module("backend.02_features.02_vault.client")
    short = _vault_client_mod.VaultClient(pool, _vault._root_key, ttl_seconds=0.1)
    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 1

    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 1

    await asyncio.sleep(0.2)
    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 2
