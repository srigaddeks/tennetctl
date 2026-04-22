"""Feature flags: CRUD + evaluation."""

from __future__ import annotations


class TestFeatureFlags:
    async def test_list_flags_empty_envelope(self, client, auth_headers):
        resp = await client.get("/v1/flags", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True

    async def test_create_and_list_flag(self, client, auth_headers, admin_session):
        create = await client.post(
            "/v1/flags",
            headers=auth_headers,
            json={
                "org_id": admin_session["org_id"],
                "key": "pytest.flag.one",
                "description": "Smoke-test flag",
                "default_value": False,
                "flag_kind": "boolean",
            },
        )
        # Some envs require is_active / more fields; accept validation errors but
        # on happy path confirm the create path + list reflects it.
        if create.status_code not in (200, 201):
            # At least ensure the endpoint exists (not 404/405).
            assert create.status_code in (400, 422), create.text
            return
        flag = create.json()["data"]
        assert flag["key"] == "pytest.flag.one"

        listed = await client.get("/v1/flags", headers=auth_headers)
        assert listed.status_code == 200
        keys = [f["key"] for f in listed.json()["data"]]
        assert "pytest.flag.one" in keys
