"""
IP allowlist integration tests.

Tests cover: list (empty), add CIDR, delete entry, invalid CIDR rejection,
IP blocking when allowlist active, IP allowed when in CIDR range.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-ipal-"
_TEST_ORG_SLUG = "ipal-test-org"
_IPAL_PATH = "/v1/iam/ip-allowlist"


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
                'DELETE FROM "04_audit"."60_evt_audit" WHERE metadata->>\'user_id\' = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


@pytest.fixture
async def live_app():
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
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="IP Allowlist Test Org")
        org_id = org["id"]

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com", display_name="IPAL User",
            )
            token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=org_id)

        try:
            yield {"app": _main.app, "pool": pool, "vault": vault, "org_id": org_id, "token": token}
        finally:
            await _cleanup(pool)


@pytest.fixture
async def authed_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        client.cookies.set("tennetctl_session", live_app["token"])
        client.headers.update({"x-org-id": live_app["org_id"]})
        yield client


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_empty(authed_client):
    resp = await authed_client.get(_IPAL_PATH)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_add_cidr(authed_client):
    resp = await authed_client.post(_IPAL_PATH, json={"cidr": "10.0.0.0/8", "label": "Private"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["cidr"] == "10.0.0.0/8"
    assert data["label"] == "Private"


@pytest.mark.asyncio
async def test_add_invalid_cidr(authed_client):
    resp = await authed_client.post(_IPAL_PATH, json={"cidr": "not-a-cidr", "label": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_entry(live_app, authed_client):
    add_resp = await authed_client.post(_IPAL_PATH, json={"cidr": "127.0.0.1/32", "label": ""})
    entry_id = add_resp.json()["data"]["id"]

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        headers={"x-org-id": live_app["org_id"], "x-forwarded-for": "127.0.0.1"},
    ) as client:
        client.cookies.set("tennetctl_session", live_app["token"])
        del_resp = await client.delete(f"{_IPAL_PATH}/{entry_id}")
        assert del_resp.status_code == 204

        list_resp = await client.get(_IPAL_PATH)
        ids = [e["id"] for e in list_resp.json()["data"]]
        assert entry_id not in ids


@pytest.mark.asyncio
async def test_ip_blocked_when_not_in_allowlist(live_app, authed_client):
    """After adding an allowlist entry, requests from an unmatched IP are blocked."""
    await authed_client.post(_IPAL_PATH, json={"cidr": "10.0.0.0/8", "label": "Private only"})

    # testclient default IP is 127.0.0.1 / testclient — not in 10.0.0.0/8
    resp = await authed_client.get(_IPAL_PATH)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "IP_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_ip_allowed_when_in_cidr(live_app, authed_client):
    """Request is allowed when source IP matches an allowlist CIDR."""
    await authed_client.post(_IPAL_PATH, json={"cidr": "127.0.0.1/32", "label": "Localhost"})

    # Testclient uses 127.0.0.1 by default
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        headers={"x-org-id": live_app["org_id"], "x-forwarded-for": "127.0.0.1"},
    ) as client:
        client.cookies.set("tennetctl_session", live_app["token"])
        resp = await client.get(_IPAL_PATH)
    assert resp.status_code == 200
