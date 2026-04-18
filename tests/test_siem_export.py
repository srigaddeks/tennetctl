"""
SIEM export integration tests.

Tests cover: list empty, create destination, update, delete, invalid kind rejection.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-siem-"
_TEST_ORG_SLUG = "siem-test-org"
_SIEM_PATH = "/v1/iam/siem-destinations"


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
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            'DELETE FROM "03_iam"."47_fct_siem_destinations" WHERE org_id IN ('
            '  SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1)',
            _TEST_ORG_SLUG,
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
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="SIEM Test Org")
        org_id = org["id"]

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com", display_name="SIEM User",
            )
            token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=org_id)

        try:
            yield {"app": _main.app, "pool": pool, "org_id": org_id, "token": token}
        finally:
            await _cleanup(pool)


@pytest.fixture
async def client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as c:
        c.cookies.set("tennetctl_session", live_app["token"])
        c.headers.update({"x-org-id": live_app["org_id"]})
        yield c


@pytest.mark.asyncio
async def test_list_empty(client):
    resp = await client.get(_SIEM_PATH)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_create_webhook(client):
    body = {"kind": "webhook", "label": "My hook", "config_jsonb": {"url": "http://localhost/hook"}}
    resp = await client.post(_SIEM_PATH, json=body)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["kind"] == "webhook"
    assert data["label"] == "My hook"


@pytest.mark.asyncio
async def test_invalid_kind(client):
    resp = await client.post(_SIEM_PATH, json={"kind": "kafka", "label": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_destination(client):
    create = await client.post(_SIEM_PATH, json={"kind": "webhook", "label": "Old", "config_jsonb": {}})
    dest_id = create.json()["data"]["id"]
    resp = await client.patch(f"{_SIEM_PATH}/{dest_id}", json={"label": "Updated", "is_active": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["label"] == "Updated"
    assert resp.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_delete_destination(client):
    create = await client.post(_SIEM_PATH, json={"kind": "s3", "label": "bucket", "config_jsonb": {}})
    dest_id = create.json()["data"]["id"]
    resp = await client.delete(f"{_SIEM_PATH}/{dest_id}")
    assert resp.status_code == 204

    list_resp = await client.get(_SIEM_PATH)
    ids = [d["id"] for d in list_resp.json()["data"]]
    assert dest_id not in ids
