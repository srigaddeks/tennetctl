"""Session management: list, revoke."""

from __future__ import annotations


class TestSessions:
    async def test_list_my_sessions_includes_current(
        self, client, admin_session
    ):
        signin = await client.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": admin_session["password"]},
        )
        assert signin.status_code == 200, signin.text
        token = signin.json()["data"]["token"]
        sess_id = signin.json()["data"]["session"]["id"]

        resp = await client.get(
            "/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        data = body["data"]
        items = data.get("items") if isinstance(data, dict) else data
        ids = [s["id"] for s in items]
        assert sess_id in ids

    async def test_signout_revokes_session(self, client, admin_session, pool):
        signin = await client.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": admin_session["password"]},
        )
        assert signin.status_code == 200, signin.text
        token = signin.json()["data"]["token"]
        sess_id = signin.json()["data"]["session"]["id"]

        out = await client.post(
            "/v1/auth/signout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert out.status_code == 200, out.text

        # Raw DB: revoked_at must be set.
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT revoked_at FROM "03_iam"."16_fct_sessions" WHERE id = $1',
                sess_id,
            )
        assert row is not None
        assert row["revoked_at"] is not None

        # And /v1/auth/me with the now-revoked token must be rejected.
        me = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 401, me.text
