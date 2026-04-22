"""IAM users CRUD."""

from __future__ import annotations


class TestIamUsers:
    async def test_list_users_includes_admin(self, client, auth_headers, admin_session):
        resp = await client.get("/v1/users", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        ids = [u["id"] for u in body["data"]]
        assert admin_session["user_id"] in ids

    async def test_get_user_returns_profile(self, client, auth_headers, admin_session):
        resp = await client.get(
            f"/v1/users/{admin_session['user_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["data"]
        assert body["id"] == admin_session["user_id"]
        assert body["email"] == admin_session["email"]

    async def test_get_user_unknown_returns_404(self, client, auth_headers):
        resp = await client.get(
            "/v1/users/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404, resp.text

    async def test_create_user_with_email_password(
        self, client, auth_headers, admin_session, pool
    ):
        resp = await client.post(
            "/v1/users",
            headers=auth_headers,
            json={
                "account_type": "email_password",
                "email": "new-user@example.com",
                "display_name": "New User",
            },
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()["data"]
        user_id = data["id"]
        assert data["email"] == "new-user@example.com"
        # Raw DB: fct has identity + account_type_id, no strings.
        async with pool.acquire() as conn:
            fct = await conn.fetchrow(
                'SELECT id, account_type_id, is_active, is_test, created_by, updated_by '
                'FROM "03_iam"."12_fct_users" WHERE id = $1',
                user_id,
            )
        assert fct is not None
        assert fct["is_active"] is True
        assert fct["created_by"] is not None

    async def test_update_user_display_name(self, client, auth_headers):
        # Create then rename.
        create = await client.post(
            "/v1/users",
            headers=auth_headers,
            json={
                "account_type": "email_password",
                "email": "rename-me@example.com",
                "display_name": "Original",
            },
        )
        assert create.status_code in (200, 201), create.text
        user_id = create.json()["data"]["id"]
        patched = await client.patch(
            f"/v1/users/{user_id}",
            headers=auth_headers,
            json={"display_name": "Renamed"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["data"]["display_name"] == "Renamed"
