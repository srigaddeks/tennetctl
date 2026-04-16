from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


InvitationService = import_module("backend.03_auth_manage.09_invitations.service").InvitationService


class InvitationEngagementMembershipAuditTests(unittest.IsolatedAsyncioTestCase):
    async def test_provision_engagement_access_writes_membership_activation_audit(self) -> None:
        service = InvitationService(
            settings=MagicMock(),
            database_pool=MagicMock(),
            cache=MagicMock(),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        conn = SimpleNamespace(
            fetchval=AsyncMock(side_effect=[1, None]),
            execute=AsyncMock(),
        )

        await service._provision_engagement_access(
            conn,
            engagement_id="11111111-1111-1111-1111-111111111111",
            user_id="22222222-2222-2222-2222-222222222222",
            email="auditor@example.com",
            tenant_key="tenant-1",
            expires_at="2026-05-01T00:00:00",
            now="2026-04-02T00:00:00",
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "engagement_membership_activated")
        self.assertEqual(audit_entry.entity_type, "engagement_membership")
        self.assertEqual(audit_entry.properties["source"], "invitation_acceptance")
        self.assertEqual(audit_entry.properties["member_email"], "auditor@example.com")


if __name__ == "__main__":
    unittest.main()
