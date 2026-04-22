"""Monitoring alert rules — verifies FIX-23 (PATCH replaces POST /pause, /unpause)."""

from __future__ import annotations

import pytest


def _valid_rule_body(name: str = "test-rule") -> dict:
    return {
        "name": name,
        "target": "metrics",
        "dsl": {"metric_key": "cpu", "timerange": {"last": "15m"}},
        "condition": {"op": "gt", "threshold": 100},
        "severity": "warn",
        "notify_template_key": "default",
        "labels": {},
    }


@pytest.fixture
async def alert_rule(client, auth_headers):
    resp = await client.post(
        "/v1/monitoring/alert-rules",
        headers=auth_headers,
        json=_valid_rule_body(),
    )
    assert resp.status_code in (200, 201), resp.text
    rule = resp.json()["data"]
    yield rule
    await client.delete(f"/v1/monitoring/alert-rules/{rule['id']}", headers=auth_headers)


class TestMonitoringAlertRules:
    async def test_create_rule_persists_with_expected_fields(self, alert_rule, pool):
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT id, org_id, name, target, severity_id, paused_until, is_active '
                'FROM "05_monitoring"."12_fct_monitoring_alert_rules" WHERE id = $1',
                alert_rule["id"],
            )
        assert row is not None
        assert row["name"] == "test-rule"
        assert row["target"] == "metrics"
        assert row["paused_until"] is None
        assert row["is_active"] is True

    async def test_patch_paused_until_sets_the_pause(self, client, auth_headers, alert_rule):
        resp = await client.patch(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}",
            headers=auth_headers,
            json={"paused_until": "2027-01-01T00:00:00"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["paused_until"] == "2027-01-01T00:00:00"

    async def test_patch_clear_paused_until_unpauses(
        self, client, auth_headers, alert_rule
    ):
        # First pause it.
        await client.patch(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}",
            headers=auth_headers,
            json={"paused_until": "2027-01-01T00:00:00"},
        )
        # Then clear via the new FIX-23 field.
        resp = await client.patch(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}",
            headers=auth_headers,
            json={"clear_paused_until": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["paused_until"] is None

    async def test_old_post_pause_endpoints_are_gone(self, client, auth_headers, alert_rule):
        """FIX-23: POST /pause and /unpause were deleted — should now 405/404."""
        pause = await client.post(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}/pause",
            headers=auth_headers,
            json={"paused_until": "2027-01-01T00:00:00"},
        )
        assert pause.status_code in (404, 405), (
            f"POST /pause must be gone (got {pause.status_code})"
        )
        unpause = await client.post(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}/unpause",
            headers=auth_headers,
        )
        assert unpause.status_code in (404, 405), (
            f"POST /unpause must be gone (got {unpause.status_code})"
        )

    async def test_patch_rename_then_list(self, client, auth_headers, alert_rule):
        resp = await client.patch(
            f"/v1/monitoring/alert-rules/{alert_rule['id']}",
            headers=auth_headers,
            json={"name": "renamed-rule"},
        )
        assert resp.status_code == 200, resp.text
        listed = await client.get("/v1/monitoring/alert-rules", headers=auth_headers)
        items = listed.json()["data"]["items"]
        match = next((r for r in items if r["id"] == alert_rule["id"]), None)
        assert match is not None
        assert match["name"] == "renamed-rule"
