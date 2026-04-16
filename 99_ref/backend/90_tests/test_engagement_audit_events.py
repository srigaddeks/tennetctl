from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock


EngagementService = import_module("backend.12_engagements.service").EngagementService


class _TransactionContext:
    def __init__(self, connection) -> None:
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeConnection:
    def transaction(self):
        return _TransactionContext(self)


class EngagementAuditEventTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repo = SimpleNamespace(
            create_engagement=AsyncMock(),
            upsert_properties=AsyncMock(),
            get_engagement_by_id=AsyncMock(
                return_value=SimpleNamespace(id="eng-1", status_code="setup")
            ),
            update_engagement=AsyncMock(),
            revoke_access_token=AsyncMock(return_value=True),
            list_access_tokens=AsyncMock(),
            create_auditor_token=AsyncMock(),
            get_open_auditor_request_id=AsyncMock(return_value=None),
            get_latest_dismissed_auditor_request_description=AsyncMock(return_value=None),
            get_latest_dismissed_auditor_request_at=AsyncMock(return_value=None),
            create_auditor_request=AsyncMock(return_value="req-1"),
            fulfill_auditor_request=AsyncMock(return_value=True),
            revoke_auditor_request_access=AsyncMock(return_value=True),
        )
        self.service = EngagementService(self.repo)
        self.service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        self.connection = _FakeConnection()

    async def test_create_auditor_request_writes_audit_event(self) -> None:
        self.repo.list_access_tokens.return_value = [
            SimpleNamespace(id="token-1", auditor_email="auditor@example.com"),
        ]

        request_id = await self.service.create_auditor_request(
            self.connection,
            engagement_id="eng-1",
            tenant_key="tenant-1",
            control_id="ctrl-1",
            email="auditor@example.com",
            description="Need proof for sampling.",
        )

        self.assertEqual(request_id, "req-1")
        self.service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_evidence_request_created")
        self.assertEqual(audit_entry.entity_id, "req-1")
        self.assertEqual(audit_entry.properties["engagement_id"], "eng-1")
        self.assertEqual(audit_entry.properties["control_id"], "ctrl-1")

    async def test_create_auditor_request_creates_token_when_missing(self) -> None:
        self.repo.list_access_tokens.return_value = []
        self.repo.create_auditor_token.return_value = SimpleNamespace(
            id="token-new",
            auditor_email="auditor@example.com",
        )

        request_id = await self.service.create_auditor_request(
            self.connection,
            engagement_id="eng-1",
            tenant_key="tenant-1",
            control_id="ctrl-1",
            email="auditor@example.com",
            description="Need proof for sampling.",
        )

        self.assertEqual(request_id, "req-1")
        self.repo.create_auditor_token.assert_awaited_once()
        create_kwargs = self.repo.create_auditor_request.await_args.kwargs
        self.assertEqual(create_kwargs["token_id"], "token-new")

    async def test_fulfill_auditor_request_writes_review_audit_event(self) -> None:
        success = await self.service.fulfill_auditor_request(
            self.connection,
            "req-1",
            "tenant-1",
            action="fulfill",
            fulfilled_by="user-1",
            attachment_id="att-1",
            response_notes="Approved for this sample.",
        )

        self.assertTrue(success)
        self.service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_evidence_request_reviewed")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["action"], "fulfill")
        self.assertEqual(audit_entry.properties["attachment_id"], "att-1")

    async def test_revoke_auditor_request_access_writes_revoke_audit_event(self) -> None:
        success = await self.service.revoke_auditor_request_access(
            self.connection,
            "req-1",
            "tenant-1",
            revoked_by="user-2",
            response_notes="Access window closed.",
        )

        self.assertTrue(success)
        self.service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_evidence_access_revoked")
        self.assertEqual(audit_entry.actor_id, "user-2")
        self.assertEqual(audit_entry.properties["response_notes"], "Access window closed.")

    async def test_create_engagement_writes_created_audit_event(self) -> None:
        request = SimpleNamespace(
            engagement_code="ENG-001",
            framework_id="11111111-1111-1111-1111-111111111111",
            framework_deployment_id="22222222-2222-2222-2222-222222222222",
            status_code="setup",
            target_completion_date=None,
            engagement_name="FY26 External Audit",
            auditor_firm="Audit Co",
            engagement_type="external",
            scope_description=None,
            audit_period_start=None,
            audit_period_end=None,
            lead_grc_sme=None,
        )

        await self.service.create_engagement(
            self.connection,
            tenant_key="tenant-1",
            org_id="33333333-3333-3333-3333-333333333333",
            data=request,
            created_by="44444444-4444-4444-4444-444444444444",
        )

        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_created")
        self.assertEqual(audit_entry.entity_type, "engagement")
        self.assertEqual(audit_entry.properties["engagement_code"], "ENG-001")

    async def test_update_engagement_writes_updated_audit_event(self) -> None:
        request = SimpleNamespace(
            status_code="active",
            target_completion_date=None,
            engagement_name="Updated Name",
            auditor_firm=None,
            scope_description=None,
            audit_period_start=None,
            audit_period_end=None,
            lead_grc_sme=None,
        )

        await self.service.update_engagement(
            self.connection,
            "eng-1",
            "tenant-1",
            data=request,
            updated_by="user-1",
        )

        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_updated")
        self.assertEqual(audit_entry.entity_id, "eng-1")
        self.assertEqual(audit_entry.properties["status_code"], "active")

    async def test_revoke_access_token_writes_audit_event(self) -> None:
        success = await self.service.revoke_access_token(
            self.connection,
            "token-1",
            "tenant-1",
            revoked_by="user-1",
        )

        self.assertTrue(success)
        audit_entry = self.service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_access_token_revoked")
        self.assertEqual(audit_entry.entity_id, "token-1")


if __name__ == "__main__":
    unittest.main()
