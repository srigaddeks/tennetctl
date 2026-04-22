"""IAM orgs + workspaces: multi-tenancy primitives."""

from __future__ import annotations


class TestOrgsAndWorkspaces:
    async def test_list_workspaces_shows_default(self, client, auth_headers, admin_session):
        resp = await client.get("/v1/workspaces", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        ids = [w["id"] for w in body["data"]]
        assert admin_session["workspace_id"] in ids

    async def test_workspace_scoped_to_org(self, client, auth_headers, admin_session, pool):
        """The workspace created in setup must be owned by the admin's org."""
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT org_id FROM "03_iam"."11_fct_workspaces" WHERE id = $1',
                admin_session["workspace_id"],
            )
        assert row is not None
        assert row["org_id"] == admin_session["org_id"]

    async def test_create_second_workspace_and_soft_delete(
        self, client, auth_headers, admin_session
    ):
        create = await client.post(
            "/v1/workspaces",
            headers=auth_headers,
            json={
                "org_id": admin_session["org_id"],
                "slug": "scratch",
                "display_name": "Scratch",
            },
        )
        assert create.status_code in (200, 201), create.text
        ws_id = create.json()["data"]["id"]

        # It should show up in list.
        listed = await client.get("/v1/workspaces", headers=auth_headers)
        assert listed.status_code == 200
        assert ws_id in [w["id"] for w in listed.json()["data"]]

        # Delete (soft) returns 204 and the row drops out of the list view.
        delete = await client.delete(f"/v1/workspaces/{ws_id}", headers=auth_headers)
        # Some delete routes return 200 with envelope, some 204. Accept both.
        assert delete.status_code in (200, 204), delete.text

        after = await client.get("/v1/workspaces", headers=auth_headers)
        assert after.status_code == 200
        assert ws_id not in [w["id"] for w in after.json()["data"]]
