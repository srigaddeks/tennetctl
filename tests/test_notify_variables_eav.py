"""Notify template variables — exercises the FIX-8 Pure-EAV split.

After the 082 migration:
- 13_fct_notify_template_variables has no strings, no JSONB.
- 23_dtl_notify_template_variables carries name/static_value/sql_template/
  param_bindings/description.
- 06_dim_notify_variable_types resolves static vs dynamic_sql.
- v_notify_template_variables joins everything back for the read path.

Uses raw DB inserts for the upstream rows (template group + template) so the
test doesn't depend on the notify admin API shape, which we haven't covered
with fixtures yet.
"""

from __future__ import annotations

import uuid

import pytest
from importlib import import_module

_uuid7 = import_module("backend.01_core.id").uuid7


@pytest.fixture
async def template_with_group(pool, admin_session):
    """Insert a template group + template via raw SQL; yield the template_id."""
    org_id = admin_session["org_id"]
    created_by = admin_session["user_id"]
    tg_id = _uuid7()
    tpl_id = _uuid7()
    async with pool.acquire() as conn:
        # Ensure a category exists (seeded) — pick id=1 (product) per default seeds.
        cat = await conn.fetchrow(
            'SELECT id FROM "06_notify"."02_dim_notify_categories" LIMIT 1'
        )
        if cat is None:
            # Seed a row in case the category dim is empty in this test DB.
            await conn.execute(
                'INSERT INTO "06_notify"."02_dim_notify_categories" (id, code, label, description) '
                "VALUES (1, 'product', 'Product', 'Product notifications')"
            )
            cat_id = 1
        else:
            cat_id = cat["id"]

        await conn.execute(
            'INSERT INTO "06_notify"."11_fct_notify_template_groups" '
            "(id, org_id, key, label, category_id, is_active, created_by, updated_by) "
            "VALUES ($1, $2, $3, $4, $5, TRUE, $6, $6)",
            tg_id, org_id, "pytest-group", "Pytest Group", cat_id, created_by,
        )
        await conn.execute(
            'INSERT INTO "06_notify"."12_fct_notify_templates" '
            "(id, org_id, key, group_id, subject, priority_id, is_active, created_by, updated_by) "
            "VALUES ($1, $2, $3, $4, $5, 2, TRUE, $6, $6)",
            tpl_id, org_id, "pytest-template", tg_id, "Hello {{name}}", created_by,
        )
    yield {"template_id": tpl_id, "group_id": tg_id, "org_id": org_id}
    # Cleanup: remove template + group. CASCADE on dtl_notify_template_variables
    # will sweep any test-created vars.
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."13_fct_notify_template_variables" WHERE template_id = $1',
            tpl_id,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE id = $1', tpl_id,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE id = $1', tg_id,
        )


class TestNotifyVariablesEav:
    async def test_fct_has_no_strings_or_jsonb(self, pool):
        """FIX-8: 13_fct_notify_template_variables must be identity-only."""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = '06_notify' "
                "AND table_name = '13_fct_notify_template_variables'"
            )
        banned = [
            r["column_name"]
            for r in rows
            if r["data_type"] in ("text", "jsonb")
        ]
        assert banned == [], f"fct must have no text/jsonb cols; found {banned}"

    async def test_dim_notify_variable_types_seeded(self, pool):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT id, code FROM "06_notify"."06_dim_notify_variable_types" '
                "ORDER BY id"
            )
        codes = [r["code"] for r in rows]
        assert "static" in codes
        assert "dynamic_sql" in codes

    async def test_create_static_variable_via_api(
        self, client, auth_headers, template_with_group, pool
    ):
        tpl_id = template_with_group["template_id"]
        resp = await client.post(
            f"/v1/notify/templates/{tpl_id}/variables",
            headers=auth_headers,
            json={
                "name": "name",
                "var_type": "static",
                "static_value": "World",
                "description": "Recipient display name",
            },
        )
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()["data"]
        assert body["name"] == "name"
        assert body["var_type"] == "static"
        assert body["static_value"] == "World"

        # Verify split persistence: identity on fct, strings on dtl.
        async with pool.acquire() as conn:
            fct = await conn.fetchrow(
                'SELECT id, template_id, org_id, var_type_id, is_active, created_by, updated_by '
                'FROM "06_notify"."13_fct_notify_template_variables" '
                "WHERE template_id = $1",
                tpl_id,
            )
            dtl = await conn.fetchrow(
                'SELECT variable_id, template_id, name, static_value, description '
                'FROM "06_notify"."23_dtl_notify_template_variables" '
                "WHERE template_id = $1",
                tpl_id,
            )
        assert fct is not None
        assert fct["var_type_id"] == 1  # static
        assert fct["is_active"] is True
        assert fct["org_id"] == template_with_group["org_id"]
        assert dtl is not None
        assert dtl["variable_id"] == fct["id"]
        assert dtl["name"] == "name"
        assert dtl["static_value"] == "World"
        assert dtl["description"] == "Recipient display name"

    async def test_list_variables_reads_via_view(
        self, client, auth_headers, template_with_group
    ):
        tpl_id = template_with_group["template_id"]
        # Seed two vars.
        for (name, val) in [("greeting", "Hi"), ("name", "Ada")]:
            r = await client.post(
                f"/v1/notify/templates/{tpl_id}/variables",
                headers=auth_headers,
                json={"name": name, "var_type": "static", "static_value": val},
            )
            assert r.status_code in (200, 201), r.text

        listed = await client.get(
            f"/v1/notify/templates/{tpl_id}/variables",
            headers=auth_headers,
        )
        assert listed.status_code == 200, listed.text
        items = listed.json()["data"]
        # Response shape may be {"items": [...]} or [...]; accept both.
        rows = items["items"] if isinstance(items, dict) else items
        names = sorted(r["name"] for r in rows)
        assert names == ["greeting", "name"]
