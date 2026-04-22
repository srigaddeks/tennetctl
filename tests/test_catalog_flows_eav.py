"""Catalog flows — end-to-end exercise of the Pure-EAV split.

Confirms that:
- POST /v1/flows writes identity to 10_fct_flows (NO strings) AND strings
  to 20_dtl_flows (via the new repository.create_flow).
- GET /v1/flows reads from v_flows which joins fct+dtl+status dim.
- PATCH /v1/flows/{id} with {name, description} updates 20_dtl_flows only,
  leaving fct unchanged apart from updated_by/updated_at.
- DELETE sets deleted_at on both fct and dtl (soft delete).
"""

from __future__ import annotations

import pytest


@pytest.fixture
async def flow(client, auth_headers):
    """Create a flow for each test and yield it; delete after."""
    resp = await client.post(
        "/v1/flows",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"slug": "test-flow", "name": "Test Flow", "description": "For pytest"},
    )
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()["data"]
    # service.create_flow returns {flow, version}; route wraps it.
    flow_payload = data.get("flow", data)
    assert flow_payload["id"]
    assert flow_payload["slug"] == "test-flow"
    yield flow_payload
    # Cleanup
    await client.delete(f"/v1/flows/{flow_payload['id']}", headers=auth_headers)


class TestCatalogFlowsEav:
    async def test_create_writes_identity_to_fct_and_strings_to_dtl(
        self, flow, pool
    ):
        async with pool.acquire() as conn:
            fct = await conn.fetchrow(
                'SELECT id, status_id, is_active, is_test, created_by, updated_by, current_version_id '
                'FROM "01_catalog"."10_fct_flows" WHERE id = $1',
                flow["id"],
            )
            dtl = await conn.fetchrow(
                'SELECT flow_id, slug, name, description '
                'FROM "01_catalog"."20_dtl_flows" WHERE flow_id = $1',
                flow["id"],
            )
        assert fct is not None, "fct row must exist"
        assert fct["is_active"] is True
        assert fct["is_test"] is False
        assert fct["created_by"] is not None
        assert fct["updated_by"] is not None
        assert fct["status_id"] == 1  # draft
        assert fct["current_version_id"] is not None

        assert dtl is not None, "dtl row must exist"
        assert dtl["slug"] == "test-flow"
        assert dtl["name"] == "Test Flow"
        assert dtl["description"] == "For pytest"

    async def test_fct_table_carries_no_string_columns(self, pool):
        """Rule: no strings on fct_*. Confirm 10_fct_flows has none."""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = '01_catalog' AND table_name = '10_fct_flows' "
                "ORDER BY ordinal_position"
            )
        string_cols = [
            r["column_name"]
            for r in rows
            if r["data_type"] in ("text", "character varying", "character")
            and r["column_name"] not in ("id", "org_id", "workspace_id", "created_by", "updated_by", "current_version_id")
        ]
        assert string_cols == [], f"fct_flows must have no business strings; found {string_cols}"

    async def test_list_returns_flow_with_joined_strings(self, client, auth_headers, flow):
        resp = await client.get("/v1/flows", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        flows = resp.json()["data"]
        match = next((f for f in flows if f["id"] == flow["id"]), None)
        assert match is not None
        assert match["slug"] == "test-flow"
        assert match["name"] == "Test Flow"
        assert match["description"] == "For pytest"
        assert match["status"] == "draft"
        assert match["current_version_id"]

    async def test_patch_name_updates_dtl_not_fct_strings(
        self, client, auth_headers, flow, pool
    ):
        patched = await client.patch(
            f"/v1/flows/{flow['id']}",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={"name": "Renamed Flow", "description": "Updated"},
        )
        assert patched.status_code == 200, patched.text

        async with pool.acquire() as conn:
            dtl = await conn.fetchrow(
                'SELECT name, description FROM "01_catalog"."20_dtl_flows" WHERE flow_id = $1',
                flow["id"],
            )
        assert dtl["name"] == "Renamed Flow"
        assert dtl["description"] == "Updated"

        # And the view picks it up.
        got = await client.get(f"/v1/flows/{flow['id']}", headers=auth_headers)
        assert got.status_code == 200
        payload = got.json()["data"]["flow"]
        assert payload["name"] == "Renamed Flow"
        assert payload["description"] == "Updated"

    async def test_initial_draft_version_created(self, flow, pool):
        async with pool.acquire() as conn:
            versions = await conn.fetch(
                'SELECT id, version_number, status_id, org_id, created_by, updated_by '
                'FROM "01_catalog"."11_fct_flow_versions" WHERE flow_id = $1',
                flow["id"],
            )
        assert len(versions) == 1, "create_flow must produce v1 draft"
        v = versions[0]
        assert v["version_number"] == 1
        assert v["status_id"] == 1  # draft
        assert v["org_id"] is not None
        assert v["created_by"] is not None
        assert v["updated_by"] is not None

    async def test_soft_delete_sets_both_fct_and_dtl_deleted_at(
        self, client, auth_headers, pool
    ):
        create = await client.post(
            "/v1/flows",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={"slug": "ephemeral", "name": "Ephemeral", "description": "will be deleted"},
        )
        assert create.status_code in (200, 201), create.text
        flow_id = create.json()["data"].get("flow", create.json()["data"])["id"]

        delete = await client.delete(f"/v1/flows/{flow_id}", headers=auth_headers)
        assert delete.status_code in (200, 204), delete.text

        async with pool.acquire() as conn:
            fct_deleted = await conn.fetchval(
                'SELECT deleted_at FROM "01_catalog"."10_fct_flows" WHERE id = $1',
                flow_id,
            )
            dtl_deleted = await conn.fetchval(
                'SELECT deleted_at FROM "01_catalog"."20_dtl_flows" WHERE flow_id = $1',
                flow_id,
            )
        assert fct_deleted is not None, "fct.deleted_at must be set"
        assert dtl_deleted is not None, "dtl.deleted_at must be set (mirrors for slug uniqueness)"

        # List view must hide it.
        listed = await client.get("/v1/flows", headers=auth_headers)
        assert flow_id not in [f["id"] for f in listed.json()["data"]]

    async def test_slug_unique_per_org(self, client, auth_headers):
        a = await client.post(
            "/v1/flows",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={"slug": "dup-slug", "name": "First", "description": ""},
        )
        assert a.status_code in (200, 201), a.text
        try:
            b = await client.post(
                "/v1/flows",
                headers={**auth_headers, "Content-Type": "application/json"},
                json={"slug": "dup-slug", "name": "Second", "description": ""},
            )
            # Partial unique index on (org_id, slug) WHERE deleted_at IS NULL must trip.
            assert b.status_code in (400, 409, 422, 500), b.text
        finally:
            flow_id = a.json()["data"].get("flow", a.json()["data"])["id"]
            await client.delete(f"/v1/flows/{flow_id}", headers=auth_headers)
