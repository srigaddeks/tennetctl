"""Integration tests for featureflags.flags."""
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

_FLAG_PREFIX = "itest_ff_"
_TEST_ORG_SLUGS = ("itest-ff-org-a",)
_TEST_APP_CODES = ("itest_ff_app_a",)


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Find flag ids with our test prefix
        flag_rows = await conn.fetch(
            'SELECT id FROM "09_featureflags"."10_fct_flags" WHERE flag_key LIKE $1',
            f"{_FLAG_PREFIX}%",
        )
        flag_ids = [r["id"] for r in flag_rows]

        org_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_ORG_SLUGS),
        )
        org_ids = [r["id"] for r in org_rows]

        # Apps with test codes
        app_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 6 AND d.code = 'code'
              AND a.key_text = ANY($1::text[])
            """,
            list(_TEST_APP_CODES),
        )
        app_ids = [r["id"] for r in app_rows]

        if flag_ids:
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

        if app_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE event_key LIKE 'iam.applications.%' AND metadata->>'application_id' = ANY($1::text[])",
                app_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=6 AND entity_id = ANY($1::text[])',
                app_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."15_fct_applications" WHERE id = ANY($1::text[])',
                app_ids,
            )

        if org_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE event_key LIKE 'iam.orgs.%' AND metadata->>'org_id' = ANY($1::text[])",
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=1 AND entity_id = ANY($1::text[])',
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."10_fct_orgs" WHERE id = ANY($1::text[])',
                org_ids,
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


async def _create_org(client: AsyncClient, slug: str) -> str:
    r = await client.post("/v1/orgs", json={"slug": slug, "display_name": slug})
    assert r.status_code == 201
    return r.json()["data"]["id"]


async def _create_app(client: AsyncClient, org_id: str, code: str) -> str:
    r = await client.post(
        "/v1/applications",
        json={"org_id": org_id, "code": code, "label": code},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.mark.asyncio
async def test_flag_crud_global(live_app) -> None:
    client, pool = live_app

    # POST global
    r = await client.post(
        "/v1/flags",
        json={
            "scope": "global",
            "flag_key": f"{_FLAG_PREFIX}global_toggle",
            "value_type": "boolean",
            "default_value": False,
            "description": "Global test flag",
        },
    )
    assert r.status_code == 201, r.text
    flag = r.json()["data"]
    flag_id = flag["id"]
    assert flag["scope"] == "global"
    assert flag["org_id"] is None
    assert flag["application_id"] is None
    assert flag["default_value"] is False

    # 4 states auto-provisioned
    r = await client.get(f"/v1/flag-states?flag_id={flag_id}")
    assert r.status_code == 200
    states = r.json()["data"]
    assert len(states) == 4
    for s in states:
        assert s["is_enabled"] is False
        assert s["environment"] in ("dev", "staging", "prod", "test")

    # Audit event
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key='featureflags.flags.created' AND metadata->>'flag_id'=$1",
            flag_id,
        )
    assert count == 1

    # GET one
    r = await client.get(f"/v1/flags/{flag_id}")
    assert r.status_code == 200
    assert r.json()["data"]["flag_key"] == f"{_FLAG_PREFIX}global_toggle"

    # List scope=global returns our flag
    r = await client.get("/v1/flags?scope=global&limit=500")
    assert r.status_code == 200
    keys = [f["flag_key"] for f in r.json()["data"]]
    assert f"{_FLAG_PREFIX}global_toggle" in keys

    # PATCH default_value
    r = await client.patch(
        f"/v1/flags/{flag_id}",
        json={"default_value": True, "description": "Updated"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["default_value"] is True

    # DELETE
    r = await client.delete(f"/v1/flags/{flag_id}")
    assert r.status_code == 204

    # Re-GET → 404
    r = await client.get(f"/v1/flags/{flag_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_flag_crud_org_and_app_scopes(live_app) -> None:
    client, _pool = live_app
    org_id = await _create_org(client, "itest-ff-org-a")
    app_id = await _create_app(client, org_id, "itest_ff_app_a")

    shared_key = f"{_FLAG_PREFIX}shared"

    # Global
    r = await client.post(
        "/v1/flags",
        json={"scope": "global", "flag_key": shared_key, "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 201

    # Org-scoped with SAME key
    r = await client.post(
        "/v1/flags",
        json={"scope": "org", "org_id": org_id, "flag_key": shared_key, "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 201
    org_flag_id = r.json()["data"]["id"]

    # App-scoped with SAME key
    r = await client.post(
        "/v1/flags",
        json={
            "scope": "application",
            "org_id": org_id,
            "application_id": app_id,
            "flag_key": shared_key,
            "value_type": "boolean",
            "default_value": False,
        },
    )
    assert r.status_code == 201
    app_flag_id = r.json()["data"]["id"]

    assert org_flag_id != app_flag_id

    # List scope=org&org_id=<a> returns only the org one
    r = await client.get(f"/v1/flags?scope=org&org_id={org_id}&limit=500")
    ids = [f["id"] for f in r.json()["data"]]
    assert org_flag_id in ids
    assert app_flag_id not in ids

    # List scope=application&application_id=<app> returns only the app one
    r = await client.get(f"/v1/flags?scope=application&application_id={app_id}&limit=500")
    ids = [f["id"] for f in r.json()["data"]]
    assert app_flag_id in ids
    assert org_flag_id not in ids


@pytest.mark.asyncio
async def test_flag_scope_target_check_violations(live_app) -> None:
    client, _pool = live_app
    org_id = await _create_org(client, "itest-ff-org-a")
    app_id = await _create_app(client, org_id, "itest_ff_app_a")

    # global with org_id → 422
    r = await client.post(
        "/v1/flags",
        json={"scope": "global", "org_id": org_id, "flag_key": f"{_FLAG_PREFIX}bad1", "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 422

    # application without application_id → 422
    r = await client.post(
        "/v1/flags",
        json={"scope": "application", "org_id": org_id, "flag_key": f"{_FLAG_PREFIX}bad2", "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 422

    # Cross-check (app's org_id != provided org_id) covered by the FK resolution
    # inside iam.applications.get + service-layer org_id assertion; not re-asserted here.
    _ = (org_id, app_id)  # mark used


@pytest.mark.asyncio
async def test_flag_unknown_parent_rejected(live_app) -> None:
    client, _pool = live_app
    missing = "00000000-0000-0000-0000-000000000000"

    r = await client.post(
        "/v1/flags",
        json={"scope": "org", "org_id": missing, "flag_key": f"{_FLAG_PREFIX}orphan", "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 404

    # For app scope: provide real org but fake app id
    org_id = await _create_org(client, "itest-ff-org-a")
    r = await client.post(
        "/v1/flags",
        json={
            "scope": "application",
            "org_id": org_id,
            "application_id": missing,
            "flag_key": f"{_FLAG_PREFIX}orphan_app",
            "value_type": "boolean",
            "default_value": False,
        },
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_flag_state_toggle(live_app) -> None:
    client, pool = live_app

    r = await client.post(
        "/v1/flags",
        json={
            "scope": "global",
            "flag_key": f"{_FLAG_PREFIX}toggle_me",
            "value_type": "boolean",
            "default_value": False,
        },
    )
    flag_id = r.json()["data"]["id"]

    r = await client.get(f"/v1/flag-states?flag_id={flag_id}")
    states = r.json()["data"]
    assert len(states) == 4
    dev_state = next(s for s in states if s["environment"] == "dev")
    assert dev_state["is_enabled"] is False

    # PATCH the dev state
    r = await client.patch(
        f"/v1/flag-states/{dev_state['id']}",
        json={"is_enabled": True},
    )
    assert r.status_code == 200
    assert r.json()["data"]["is_enabled"] is True

    # Audit event
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key='featureflags.flags.state_updated' AND metadata->>'state_id'=$1",
            dev_state["id"],
        )
    assert count == 1

    # Re-GET states; dev is now enabled
    r = await client.get(f"/v1/flag-states?flag_id={flag_id}")
    dev = next(s for s in r.json()["data"] if s["environment"] == "dev")
    assert dev["is_enabled"] is True


@pytest.mark.asyncio
async def test_featureflags_flags_via_run_node(live_app) -> None:
    _client, pool = live_app

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup", trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "featureflags.flags.create", ctx,
                {
                    "scope": "global",
                    "flag_key": f"{_FLAG_PREFIX}node_global",
                    "value_type": "boolean",
                    "default_value": True,
                },
            )
    flag = result["flag"]
    assert flag["flag_key"] == f"{_FLAG_PREFIX}node_global"
    assert flag["default_value"] is True

    # Get via node
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t2", span_id="s2",
            conn=conn, extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "featureflags.flags.get", ctx, {"id": flag["id"]})
    assert got["flag"]["id"] == flag["id"]

    # Missing id → None
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t3", span_id="s3",
            conn=conn, extras={"pool": pool},
        )
        missing = await _catalog.run_node(
            pool, "featureflags.flags.get", ctx,
            {"id": "00000000-0000-0000-0000-000000000000"},
        )
    assert missing == {"flag": None}
