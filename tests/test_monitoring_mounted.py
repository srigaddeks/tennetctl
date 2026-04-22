"""Every monitoring sub-feature router must be mounted and respond.

Regression test for commit 55b2c81 which wired 08_escalation, 09_action_templates,
10_incidents, 11_slo, and 12_dashboard_sharing into the monitoring router.
Each endpoint should return a 2xx with an empty envelope for a fresh DB.
"""

from __future__ import annotations


class TestMonitoringRoutersMounted:
    async def test_alert_rules_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/alert-rules", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    async def test_escalation_policies_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/escalation-policies", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    async def test_oncall_schedules_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/oncall-schedules", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    async def test_action_templates_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/action-templates", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    async def test_incidents_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/incidents", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    async def test_slos_list(self, client, auth_headers):
        resp = await client.get("/v1/monitoring/slos", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True
