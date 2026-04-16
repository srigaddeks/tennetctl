"""
Integration tests for vault.secrets — plan 07-01 AC-3/4/5/7/8/9.

Runs against the LIVE tennetctl DB (pattern mirrors test_iam_orgs_api.py).
Each test cleans up its rows in setup + teardown.

Reverse-search guards:
  - test_plaintext_never_logged    — caplog grep for the sentinel
  - test_ciphertext_is_binary      — DB scan confirms plaintext isn't stored
  - test_list_has_no_value         — HTTP list response never carries value
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import replace
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
            'SELECT id, key, version, ciphertext, deleted_at '
            'FROM "02_vault"."10_fct_vault_entries" '
            'WHERE key = $1 ORDER BY version',
            key,
        )
        return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# AC-3: full CRUD via HTTP
# ─────────────────────────────────────────────────────────────────────

async def test_crud_round_trip(live_app) -> None:
    client, pool, _vault = live_app
    key = f"{_PREFIX}crud"

    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "hunter2", "description": "crud test"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ok"] is True
    meta = body["data"]
    assert meta["key"] == key
    assert meta["version"] == 1
    assert meta["description"] == "crud test"
    assert "value" not in meta
    assert "ciphertext" not in meta

    resp = await client.get("/v1/vault")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    items = payload["data"]
    # Every list row is metadata only — no value / ciphertext / wrapped_dek / nonce.
    for item in items:
        for forbidden in ("value", "ciphertext", "wrapped_dek", "nonce"):
            assert forbidden not in item

    resp = await client.get(f"/v1/vault/{key}")
    assert resp.status_code == 200
    assert resp.json()["data"]["value"] == "hunter2"
    assert resp.json()["data"]["version"] == 1

    resp = await client.post(
        f"/v1/vault/{key}/rotate",
        json={"value": "hunter3"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["version"] == 2

    resp = await client.get(f"/v1/vault/{key}")
    assert resp.json()["data"]["value"] == "hunter3"
    assert resp.json()["data"]["version"] == 2

    resp = await client.delete(f"/v1/vault/{key}")
    assert resp.status_code == 204

    resp = await client.get(f"/v1/vault/{key}")
    assert resp.status_code == 404
    assert resp.json()["ok"] is False
    assert resp.json()["error"]["code"] == "NOT_FOUND"


# ─────────────────────────────────────────────────────────────────────
# AC-3 audit emission
# ─────────────────────────────────────────────────────────────────────

async def test_audit_events_emitted(live_app) -> None:
    client, pool, _vault = live_app
    key = f"{_PREFIX}audit"

    resp = await client.post(
        "/v1/vault",
        json={"key": key, "value": "x", "description": "audit"},
    )
    assert resp.status_code == 201
    assert await _count_events(pool, "vault.secrets.created", key) == 1

    resp = await client.get(f"/v1/vault/{key}")
    assert resp.status_code == 200
    assert await _count_events(pool, "vault.secrets.read", key) == 1

    resp = await client.post(f"/v1/vault/{key}/rotate", json={"value": "y"})
    assert resp.status_code == 200
    assert await _count_events(pool, "vault.secrets.rotated", key) == 1

    resp = await client.delete(f"/v1/vault/{key}")
    assert resp.status_code == 204
    assert await _count_events(pool, "vault.secrets.deleted", key) == 1


# ─────────────────────────────────────────────────────────────────────
# AC-3 / AC-4 — reads fail on deleted + cache is busted
# ─────────────────────────────────────────────────────────────────────

async def test_cannot_read_deleted(live_app) -> None:
    client, _pool, vault = live_app
    key = f"{_PREFIX}del"

    await client.post("/v1/vault", json={"key": key, "value": "gone"})
    # Warm the cache via the in-process client.
    assert await vault.get(key) == "gone"

    await client.delete(f"/v1/vault/{key}")
    # In-process client bypasses HTTP — invalidate is called by the service.
    with pytest.raises(_client_mod.VaultSecretNotFound):
        await vault.get(key)


# ─────────────────────────────────────────────────────────────────────
# AC-3 key recycling refused in v0.2
# ─────────────────────────────────────────────────────────────────────

async def test_key_recycling_refused(live_app) -> None:
    client, _pool, _vault = live_app
    key = f"{_PREFIX}recycle"

    resp = await client.post("/v1/vault", json={"key": key, "value": "first"})
    assert resp.status_code == 201

    resp = await client.delete(f"/v1/vault/{key}")
    assert resp.status_code == 204

    resp = await client.post("/v1/vault", json={"key": key, "value": "second"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


# ─────────────────────────────────────────────────────────────────────
# AC-6 key shape validation
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_key", [
    "UPPER.key",     # uppercase
    "1leading-digit",  # starts with digit
    "_underscore",   # starts with underscore (regex requires letter)
    "spa ced",       # space
    "slash/bad",     # slash
    "a" * 129,       # too long (max 128)
])
async def test_key_shape_rejected(live_app, bad_key: str) -> None:
    client, _pool, _vault = live_app
    resp = await client.post("/v1/vault", json={"key": bad_key, "value": "x"})
    assert resp.status_code == 422, f"bad_key={bad_key!r} got {resp.status_code}"


# ─────────────────────────────────────────────────────────────────────
# AC-3 empty value
# ─────────────────────────────────────────────────────────────────────

async def test_empty_value_rejected(live_app) -> None:
    client, _pool, _vault = live_app
    resp = await client.post(
        "/v1/vault",
        json={"key": f"{_PREFIX}empty", "value": ""},
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# AC-5 run_node for put/get/rotate/delete
# ─────────────────────────────────────────────────────────────────────

async def test_nodes_via_runner(live_app) -> None:
    _client, pool, vault = live_app
    key = f"{_PREFIX}nodes"

    # put (effect, tx=caller) — open tx, attach conn
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
                {"key": key, "value": "node-v1", "description": "via node"},
            )
    assert "secret" in result and result["secret"]["key"] == key
    assert result["secret"]["version"] == 1
    assert await _count_events(pool, "vault.secrets.created", key) == 1

    # get (request, tx=none) — no conn injection
    ctx = _ctx_mod.NodeContext(
        audit_category="system",
        trace_id="t-vn-2", span_id="s-vn-2",
        extras={"vault": vault},
    )
    got = await _catalog.run_node(pool, "vault.secrets.get", ctx, {"key": key})
    assert got == {"value": "node-v1", "version": 1}
    # vault.secrets.get is emits_audit=false — no audit row for it.
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
                {"key": key, "value": "node-v2"},
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
            await _catalog.run_node(pool, "vault.secrets.delete", ctx, {"key": key})
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
        json={"key": key, "value": sentinel, "description": "log check"},
    )
    await client.get(f"/v1/vault/{key}")
    await client.post(f"/v1/vault/{key}/rotate", json={"value": sentinel + "-b"})
    await client.delete(f"/v1/vault/{key}")

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

    await client.post("/v1/vault", json={"key": key, "value": sentinel})
    rows = await _fetch_row(pool, key)
    assert len(rows) == 1
    ct = bytes(rows[0]["ciphertext"])
    # Sentinel must not appear anywhere in the stored ciphertext.
    assert sentinel.encode("utf-8") not in ct
    # Ciphertext length = plaintext length + 16 byte GCM tag.
    assert len(ct) == len(sentinel) + 16


# ─────────────────────────────────────────────────────────────────────
# AC-4 cache refresh on rotate
# ─────────────────────────────────────────────────────────────────────

async def test_cache_refresh_on_rotate(live_app) -> None:
    client, _pool, vault = live_app
    key = f"{_PREFIX}cache"

    await client.post("/v1/vault", json={"key": key, "value": "v1"})
    assert await vault.get(key) == "v1"
    before = vault._fetch_count

    # Second call within TTL — no DB hit.
    assert await vault.get(key) == "v1"
    assert vault._fetch_count == before

    # Rotate via HTTP — service invalidates cache.
    await client.post(f"/v1/vault/{key}/rotate", json={"value": "v2"})
    assert await vault.get(key) == "v2"
    assert vault._fetch_count == before + 1


# ─────────────────────────────────────────────────────────────────────
# AC-4 cache TTL expiry
# ─────────────────────────────────────────────────────────────────────

async def test_cache_ttl_expiry(live_app) -> None:
    client, pool, _vault = live_app
    key = f"{_PREFIX}ttl"

    await client.post("/v1/vault", json={"key": key, "value": "ttl-v1"})

    # Use a short-TTL client pointing at the same pool + root key.
    _vault_client_mod = import_module("backend.02_features.02_vault.client")
    short = _vault_client_mod.VaultClient(pool, _vault._root_key, ttl_seconds=0.1)
    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 1

    # Cached read — same fetch count.
    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 1

    # Wait out the TTL; next read hits the DB again.
    await asyncio.sleep(0.2)
    assert await short.get(key) == "ttl-v1"
    assert short._fetch_count == 2
