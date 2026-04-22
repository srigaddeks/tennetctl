"""Audit events: mutations in other features must produce audit rows."""

from __future__ import annotations


class TestAuditEvents:
    async def test_workspace_creation_emits_audit_event(
        self, client, auth_headers, admin_session, pool
    ):
        # Snapshot counter before.
        async with pool.acquire() as conn:
            before = await conn.fetchval(
                'SELECT COUNT(*) FROM "04_audit"."60_evt_audit" '
                "WHERE actor_user_id = $1",
                admin_session["user_id"],
            )

        create = await client.post(
            "/v1/workspaces",
            headers=auth_headers,
            json={
                "org_id": admin_session["org_id"],
                "slug": "audit-probe",
                "display_name": "Audit Probe",
            },
        )
        assert create.status_code in (200, 201), create.text

        # Audit row must have landed.
        async with pool.acquire() as conn:
            after = await conn.fetchval(
                'SELECT COUNT(*) FROM "04_audit"."60_evt_audit" '
                "WHERE actor_user_id = $1",
                admin_session["user_id"],
            )
        assert after > before, (
            f"workspace create must emit at least one audit row (before={before}, after={after})"
        )

    async def test_audit_events_listing_endpoint(self, client, auth_headers):
        # Drive an arbitrary event first so there's at least one row.
        await client.post(
            "/v1/workspaces",
            headers=auth_headers,
            json={
                "org_id": (await client.get("/v1/orgs", headers=auth_headers)).json()["data"][0]["id"],
                "slug": "audit-list-probe",
                "display_name": "Probe",
            },
        )
        resp = await client.get("/v1/audit-events", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        # Either {"items": [...]} or {"data": [...]}; accept both shapes.
        data = body["data"]
        items = data.get("items") if isinstance(data, dict) else data
        assert isinstance(items, list)
