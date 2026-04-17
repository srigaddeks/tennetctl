"""
Integration tests for iam.users — third IAM vertical.

Covers: CRUD, invalid account_type rejection, run_node dispatch, list filters.
"""

from __future__ import annotations

import os
from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_TEST_EMAIL_PREFIX = "itest-users-"


async def _cleanup_test_rows(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Find user ids by email pattern.
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.users.%'
              AND metadata->>'user_id' = ANY($1::text[])
            """,
            user_ids,
        )
        await conn.execute(
            """
            DELETE FROM "03_iam"."21_dtl_attrs"
            WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])
            """,
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
            user_ids,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup_test_rows(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup_test_rows(pool)
            _catalog.clear_checkers()


async def _count_events(pool: Any, event_key: str, user_id: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = $1 AND metadata->>'user_id' = $2",
            event_key, user_id,
        )


@pytest.mark.asyncio
async def test_user_crud_end_to_end(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}alice@example.com"

    # POST
    resp = await client.post(
        "/v1/users",
        json={
            "account_type": "email_password",
            "email": email,
            "display_name": "Alice",
            "avatar_url": "https://img/a",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    user_id = data["id"]
    assert data["account_type"] == "email_password"
    assert data["email"] == email
    assert data["display_name"] == "Alice"
    assert data["avatar_url"] == "https://img/a"
    assert await _count_events(pool, "iam.users.created", user_id) == 1

    # DB — 3 dtl rows
    async with pool.acquire() as conn:
        attr_count = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=3 AND entity_id=$1',
            user_id,
        )
    assert attr_count == 3

    # GET
    resp = await client.get(f"/v1/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == email

    # PATCH display_name only
    resp = await client.patch(
        f"/v1/users/{user_id}",
        json={"display_name": "Alice B."},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Alice B."
    assert await _count_events(pool, "iam.users.updated", user_id) == 1

    # PATCH is_active toggle — emits iam.users.deactivated, not iam.users.updated
    resp = await client.patch(
        f"/v1/users/{user_id}",
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False
    assert await _count_events(pool, "iam.users.deactivated", user_id) == 1

    # No-op PATCH — updated count stays at 1
    resp = await client.patch(
        f"/v1/users/{user_id}",
        json={"display_name": "Alice B."},
    )
    assert resp.status_code == 200
    assert await _count_events(pool, "iam.users.updated", user_id) == 1

    # DELETE
    resp = await client.delete(f"/v1/users/{user_id}")
    assert resp.status_code == 204
    assert await _count_events(pool, "iam.users.deleted", user_id) == 1

    # GET post-delete
    resp = await client.get(f"/v1/users/{user_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_invalid_account_type_rejected(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}bad@example.com"

    resp = await client.post(
        "/v1/users",
        json={
            "account_type": "banana_oauth",
            "email": email,
            "display_name": "Bad",
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "banana_oauth" in body["error"]["message"]

    # Nothing persisted
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            """
            SELECT count(*) FROM "03_iam"."21_dtl_attrs"
            WHERE entity_type_id=3 AND key_text=$1
            """,
            email,
        )
    assert count == 0


@pytest.mark.asyncio
async def test_iam_users_create_and_get_via_run_node(live_app) -> None:
    _client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}node@example.com"

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.users.create", ctx,
                {
                    "account_type": "google_oauth",
                    "email": email,
                    "display_name": "Via Node",
                },
            )
    user = result["user"]
    user_id = user["id"]
    assert user["account_type"] == "google_oauth"
    assert user["email"] == email
    assert await _count_events(pool, "iam.users.created", user_id) == 1

    # iam.users.get — control, no audit
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t2", span_id="s2",
            conn=conn, extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "iam.users.get", ctx, {"id": user_id})
    assert got["user"] is not None
    assert got["user"]["id"] == user_id

    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t3", span_id="s3",
            conn=conn, extras={"pool": pool},
        )
        missing = await _catalog.run_node(
            pool, "iam.users.get", ctx, {"id": "00000000-0000-0000-0000-000000000000"},
        )
    assert missing == {"user": None}


@pytest.mark.asyncio
async def test_user_list_filter_by_account_type(live_app) -> None:
    client, _pool = live_app

    e1 = f"{_TEST_EMAIL_PREFIX}ep@example.com"
    e2 = f"{_TEST_EMAIL_PREFIX}gh@example.com"

    r1 = await client.post(
        "/v1/users",
        json={"account_type": "email_password", "email": e1, "display_name": "EP User"},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/v1/users",
        json={"account_type": "github_oauth", "email": e2, "display_name": "GH User"},
    )
    assert r2.status_code == 201

    # Filter: email_password only
    resp = await client.get("/v1/users?account_type=email_password&limit=500")
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()["data"]]
    assert e1 in emails
    assert e2 not in emails

    # Filter: github_oauth only
    resp = await client.get("/v1/users?account_type=github_oauth&limit=500")
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()["data"]]
    assert e2 in emails
    assert e1 not in emails
