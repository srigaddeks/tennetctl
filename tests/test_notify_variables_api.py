"""
Integration tests for notify.template_variables CRUD + resolve + render integration.

Each test is self-contained: creates its own template + variables, asserts, fixture tears down.
Function-scoped live_app fixture to avoid asyncpg cross-loop issues.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID     = "019e0000-2222-7000-0000-000000000001"
_WS_ID      = "019e0000-2222-7000-0000-000000000002"
_USER_ID    = "019e0000-2222-7000-0000-000000000003"
_SESSION_ID = "019e0000-2222-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # variables cascade-delete when templates are deleted
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE actor_user_id = $1',
            _USER_ID,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                headers=_HDR,
            ) as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _create_group(client: Any, key: str = "var-test-group") -> dict:
    r = await client.post("/v1/notify/template-groups", json={
        "org_id": _ORG_ID, "key": key, "label": "Var Test Group", "category_id": 1,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_template(
    client: Any,
    group_id: str,
    key: str = "var-test-tmpl",
    subject: str = "Test subject",
    body_html: str = "<p>Hello world</p>",
    body_text: str = "Hello world",
) -> dict:
    r = await client.post("/v1/notify/templates", json={
        "org_id": _ORG_ID, "key": key, "group_id": group_id,
        "subject": subject,
        "bodies": [{"channel_id": 1, "body_html": body_html, "body_text": body_text}],
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_static_var(
    client: Any,
    template_id: str,
    name: str = "brand",
    value: str = "ACME Corp",
) -> dict:
    r = await client.post(f"/v1/notify/templates/{template_id}/variables", json={
        "name": name, "var_type": "static", "static_value": value,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


def _make_ctx(pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        org_id=_ORG_ID,
        workspace_id=_WS_ID,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="system",
        extras={"pool": pool},
    )


# ─── CRUD tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_static_variable(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-create-static")
    tmpl = await _create_template(client, grp["id"], "t-create-static")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "brand_name", "var_type": "static", "static_value": "ACME Corp",
        "description": "Company name",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["name"] == "brand_name"
    assert data["var_type"] == "static"
    assert data["static_value"] == "ACME Corp"
    assert data["template_id"] == tmpl["id"]


@pytest.mark.asyncio
async def test_list_variables_empty(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-list-empty")
    tmpl = await _create_template(client, grp["id"], "t-list-empty")
    r = await client.get(f"/v1/notify/templates/{tmpl['id']}/variables")
    assert r.status_code == 200
    assert r.json()["data"]["items"] == []
    assert r.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_variables_returns_created(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-list-vars")
    tmpl = await _create_template(client, grp["id"], "t-list-vars")
    await _create_static_var(client, tmpl["id"], "alpha", "A")
    await _create_static_var(client, tmpl["id"], "beta", "B")
    r = await client.get(f"/v1/notify/templates/{tmpl['id']}/variables")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 2
    names = {v["name"] for v in r.json()["data"]["items"]}
    assert {"alpha", "beta"} == names


@pytest.mark.asyncio
async def test_get_variable(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-get-var")
    tmpl = await _create_template(client, grp["id"], "t-get-var")
    created = await _create_static_var(client, tmpl["id"], "greeting", "Hello")
    r = await client.get(f"/v1/notify/templates/{tmpl['id']}/variables/{created['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "greeting"
    assert r.json()["data"]["static_value"] == "Hello"


@pytest.mark.asyncio
async def test_update_variable_description(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-update-var")
    tmpl = await _create_template(client, grp["id"], "t-update-var")
    created = await _create_static_var(client, tmpl["id"], "foot_note")
    r = await client.patch(
        f"/v1/notify/templates/{tmpl['id']}/variables/{created['id']}",
        json={"description": "Updated description"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_static_value(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-update-val")
    tmpl = await _create_template(client, grp["id"], "t-update-val")
    created = await _create_static_var(client, tmpl["id"], "site_name", "Old Site")
    r = await client.patch(
        f"/v1/notify/templates/{tmpl['id']}/variables/{created['id']}",
        json={"static_value": "New Site"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["static_value"] == "New Site"


@pytest.mark.asyncio
async def test_delete_variable(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-del-var")
    tmpl = await _create_template(client, grp["id"], "t-del-var")
    created = await _create_static_var(client, tmpl["id"], "to_delete")
    r = await client.delete(f"/v1/notify/templates/{tmpl['id']}/variables/{created['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/v1/notify/templates/{tmpl['id']}/variables/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_create_dynamic_sql_variable(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-dyn-sql")
    tmpl = await _create_template(client, grp["id"], "t-dyn-sql")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "user_id_param",
        "var_type": "dynamic_sql",
        "sql_template": "SELECT $1::text",
        "param_bindings": {"$1": "actor_user_id"},
        "description": "Returns actor_user_id directly",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["var_type"] == "dynamic_sql"
    assert data["sql_template"] == "SELECT $1::text"
    assert data["param_bindings"] == {"$1": "actor_user_id"}


# ─── Safelist tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_safelist_rejects_insert(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-insert")
    tmpl = await _create_template(client, grp["id"], "t-sl-insert")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "INSERT INTO foo VALUES (1)",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_safelist_rejects_update(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-update")
    tmpl = await _create_template(client, grp["id"], "t-sl-update")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "UPDATE foo SET x = 1 WHERE id = $1",
        "param_bindings": {"$1": "actor_user_id"},
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_safelist_rejects_drop(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-drop")
    tmpl = await _create_template(client, grp["id"], "t-sl-drop")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "DROP TABLE foo",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_safelist_rejects_non_select(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-non-sel")
    tmpl = await _create_template(client, grp["id"], "t-sl-non-sel")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "EXECUTE some_procedure()",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_safelist_rejects_disallowed_param(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-param")
    tmpl = await _create_template(client, grp["id"], "t-sl-param")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "SELECT $1::text",
        "param_bindings": {"$1": "evil_key"},
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_safelist_rejects_empty_sql(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sl-empty")
    tmpl = await _create_template(client, grp["id"], "t-sl-empty")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "evil", "var_type": "dynamic_sql",
        "sql_template": "   ",
    })
    assert r.status_code == 422


# ─── Schema validation tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_variable_name_must_be_identifier(live_app):
    """Name with space is rejected (pattern ^[a-z_][a-z0-9_]*$)"""
    client, _ = live_app
    grp = await _create_group(client, "g-name-space")
    tmpl = await _create_template(client, grp["id"], "t-name-space")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "my var", "var_type": "static", "static_value": "x",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_variable_name_no_uppercase(live_app):
    """Name with uppercase is rejected"""
    client, _ = live_app
    grp = await _create_group(client, "g-name-upper")
    tmpl = await _create_template(client, grp["id"], "t-name-upper")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "Brand", "var_type": "static", "static_value": "x",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_static_requires_static_value(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-static-req")
    tmpl = await _create_template(client, grp["id"], "t-static-req")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "brand", "var_type": "static",
        # missing static_value
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_dynamic_requires_sql_template(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-dyn-req")
    tmpl = await _create_template(client, grp["id"], "t-dyn-req")
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "user_name", "var_type": "dynamic_sql",
        # missing sql_template
    })
    assert r.status_code == 422


# ─── Render integration tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_render_resolves_static_variable(live_app):
    """Registered static variable is substituted when render called with empty variables."""
    client, pool = live_app
    grp = await _create_group(client, "g-render-static")
    tmpl = await _create_template(
        client, grp["id"], "t-render-static",
        subject="Email from {{ company }}",
        body_html="<p>Sent by {{ company }}</p>",
        body_text="Sent by {{ company }}",
    )
    await _create_static_var(client, tmpl["id"], "company", "ACME Corp")

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "t-render-static",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {},  # empty — relies on registered static variable
            },
        )
    assert result["rendered_html"] == "<p>Sent by ACME Corp</p>"
    assert result["rendered_text"] == "Sent by ACME Corp"
    assert result["rendered_subject"] == "Email from ACME Corp"


@pytest.mark.asyncio
async def test_render_caller_overrides_registered(live_app):
    """Caller-supplied variables override registered static variables."""
    client, pool = live_app
    grp = await _create_group(client, "g-render-override")
    tmpl = await _create_template(
        client, grp["id"], "t-render-override",
        subject="Subject",
        body_html="<p>{{ greeting }}, world!</p>",
        body_text="{{ greeting }}, world!",
    )
    await _create_static_var(client, tmpl["id"], "greeting", "Hello")

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "t-render-override",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {"greeting": "Howdy"},  # caller overrides registered "Hello"
            },
        )
    assert "Howdy" in result["rendered_html"]
    assert "Hello" not in result["rendered_html"]


@pytest.mark.asyncio
async def test_render_no_registered_variables(live_app):
    """Template with no registered vars still renders with caller-supplied variables."""
    client, pool = live_app
    grp = await _create_group(client, "g-render-noreg")
    tmpl = await _create_template(
        client, grp["id"], "t-render-noreg",
        subject="Subject",
        body_html="<p>{{ name }}</p>",
        body_text="{{ name }}",
    )
    # No registered variables — caller provides all

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "t-render-noreg",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {"name": "World"},
            },
        )
    assert result["rendered_html"] == "<p>World</p>"


@pytest.mark.asyncio
async def test_render_dynamic_sql_variable(live_app):
    """Dynamic SQL variable (SELECT $1::text) resolved from context and injected."""
    client, pool = live_app
    grp = await _create_group(client, "g-render-dyn")
    tmpl = await _create_template(
        client, grp["id"], "t-render-dyn",
        subject="Subject",
        body_html="<p>User: {{ user_ref }}</p>",
        body_text="User: {{ user_ref }}",
    )
    # Dynamic var: SELECT $1::text with actor_user_id -> returns actor_user_id as text
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "user_ref",
        "var_type": "dynamic_sql",
        "sql_template": "SELECT $1::text",
        "param_bindings": {"$1": "actor_user_id"},
    })
    assert r.status_code == 201

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "t-render-dyn",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {},
                "context": {"actor_user_id": "test-user-abc123"},
            },
        )
    assert "test-user-abc123" in result["rendered_html"]
    assert "test-user-abc123" in result["rendered_text"]


@pytest.mark.asyncio
async def test_resolve_endpoint(live_app):
    """POST /resolve returns resolved dict of all registered variables."""
    client, _ = live_app
    grp = await _create_group(client, "g-resolve-ep")
    tmpl = await _create_template(client, grp["id"], "t-resolve-ep")
    await _create_static_var(client, tmpl["id"], "brand", "Tennet")
    await _create_static_var(client, tmpl["id"], "footer", "© 2026")

    r = await client.post(
        f"/v1/notify/templates/{tmpl['id']}/variables/resolve",
        json={"context": {}},
    )
    assert r.status_code == 200
    resolved = r.json()["data"]["resolved"]
    assert resolved["brand"] == "Tennet"
    assert resolved["footer"] == "© 2026"


@pytest.mark.asyncio
async def test_variable_unique_per_template(live_app):
    """Creating the same variable name twice for the same template is rejected."""
    client, _ = live_app
    grp = await _create_group(client, "g-uniq-var")
    tmpl = await _create_template(client, grp["id"], "t-uniq-var")
    await _create_static_var(client, tmpl["id"], "brand", "First")
    # Second with same name → DB UNIQUE constraint → 500 or 409
    r = await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "brand", "var_type": "static", "static_value": "Second",
    })
    assert r.status_code in (409, 500)  # DB unique constraint violation


@pytest.mark.asyncio
async def test_delete_cascades_on_template_delete(live_app):
    """Hard-deleting a template cascades to its variables via FK ON DELETE CASCADE."""
    client, pool = live_app
    grp = await _create_group(client, "g-cascade")
    tmpl = await _create_template(client, grp["id"], "t-cascade")
    var = await _create_static_var(client, tmpl["id"], "brand")

    # Hard-delete the template directly from fct table to trigger FK cascade.
    # (API soft-deletes only; cascade fires on real DELETE.)
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE id = $1',
            tmpl["id"],
        )

    # Variable should be gone via CASCADE DELETE
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id FROM "06_notify"."13_fct_notify_template_variables" WHERE id = $1',
            var["id"],
        )
    assert row is None
