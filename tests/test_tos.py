"""
TOS versioning integration tests.

Tests cover: no current TOS, create + mark effective, accept, gate check.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-tos-"
_TEST_ORG_SLUG = "tos-test-org"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        user_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in user_rows]
        if user_ids:
            await conn.execute(
                'DELETE FROM "03_iam"."49_lnk_user_tos_acceptance" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            'DELETE FROM "03_iam"."49_lnk_user_tos_acceptance" WHERE version_id IN ('
            '  SELECT id FROM "03_iam"."48_fct_tos_versions" WHERE version LIKE $1)',
            "itest-%",
        )
        await conn.execute(
            'DELETE FROM "03_iam"."48_fct_tos_versions" WHERE version LIKE $1', "itest-%"
        )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


@pytest.fixture
async def setup():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault
        await _cleanup(pool)

        _orgs_svc: Any = import_module("backend.02_features.03_iam.sub_features.01_orgs.service")
        _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
        _sessions_svc: Any = import_module("backend.02_features.03_iam.sub_features.09_sessions.service")
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="TOS Test Org")
        org_id = org["id"]

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com", display_name="TOS User",
            )
            token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=org_id)
        user_id = user["id"]

        try:
            yield {
                "pool": pool, "ctx": ctx, "org_id": org_id,
                "user_id": user_id, "token": token,
                "app": _main.app, "vault": vault,
            }
        finally:
            await _cleanup(pool)


@pytest.fixture
async def authed_client(setup):
    async with AsyncClient(
        transport=ASGITransport(app=setup["app"]),
        base_url="http://test",
    ) as c:
        c.cookies.set("tennetctl_session", setup["token"])
        c.headers.update({"x-org-id": setup["org_id"]})
        yield c


@pytest.mark.asyncio
async def test_no_current_tos(authed_client):
    resp = await authed_client.get("/v1/tos/current")
    assert resp.status_code == 200
    assert resp.json()["data"] is None


@pytest.mark.asyncio
async def test_create_tos_version(authed_client):
    resp = await authed_client.post("/v1/tos", json={
        "version": "itest-v1", "title": "Test TOS", "body_markdown": "# Terms",
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["version"] == "itest-v1"


@pytest.mark.asyncio
async def test_mark_effective_and_get_current(authed_client):
    create = await authed_client.post("/v1/tos", json={
        "version": "itest-v2", "title": "TOS v2", "body_markdown": "Content",
    })
    version_id = create.json()["data"]["id"]

    eff = await authed_client.post(f"/v1/tos/{version_id}/effective", json={
        "effective_at": "2020-01-01T00:00:00",
    })
    assert eff.status_code == 200
    assert eff.json()["data"]["effective_at"] is not None

    current = await authed_client.get("/v1/tos/current")
    assert current.json()["data"]["id"] == version_id


@pytest.mark.asyncio
async def test_accept_tos(setup, authed_client):
    _tos_svc: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.service")
    pool = setup["pool"]
    ctx = setup["ctx"]

    async with pool.acquire() as conn:
        v = await _tos_svc.create_version(
            pool, conn, ctx, version="itest-v3", title="TOS v3", body_markdown="",
        )
        await _tos_svc.mark_effective(pool, conn, ctx, version_id=v["id"], effective_at="2020-01-01 00:00:00")

    resp = await authed_client.post("/v1/tos/accept", json={"version_id": v["id"]})
    assert resp.status_code == 200
    assert resp.json()["data"]["accepted"] is True


@pytest.mark.asyncio
async def test_check_tos_gate_no_acceptance(setup):
    _tos_svc: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.service")
    pool = setup["pool"]
    ctx = setup["ctx"]

    async with pool.acquire() as conn:
        v = await _tos_svc.create_version(
            pool, conn, ctx, version="itest-v4", title="TOS v4", body_markdown="",
        )
        await _tos_svc.mark_effective(pool, conn, ctx, version_id=v["id"], effective_at="2020-01-01 00:00:00")
        pending = await _tos_svc.check_tos_gate(conn, user_id=setup["user_id"])
    assert pending == v["id"]


@pytest.mark.asyncio
async def test_check_tos_gate_after_acceptance(setup):
    _tos_svc: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.service")
    pool = setup["pool"]
    ctx = setup["ctx"]

    async with pool.acquire() as conn:
        v = await _tos_svc.create_version(
            pool, conn, ctx, version="itest-v5", title="TOS v5", body_markdown="",
        )
        await _tos_svc.mark_effective(pool, conn, ctx, version_id=v["id"], effective_at="2020-01-01 00:00:00")
        await _tos_svc.accept_tos(pool, conn, ctx, user_id=setup["user_id"], version_id=v["id"], client_ip=None)
        pending = await _tos_svc.check_tos_gate(conn, user_id=setup["user_id"])
    assert pending is None
