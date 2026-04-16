from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


InvitationService = import_module("backend.03_auth_manage.09_invitations.service").InvitationService
InviteScope = import_module("backend.03_auth_manage.09_invitations.service").InviteScope


class InvitationEngagementIdsAutoEnrollTests(unittest.IsolatedAsyncioTestCase):
    async def test_auto_enroll_provisions_all_engagement_ids(self) -> None:
        service = InvitationService(
            settings=MagicMock(),
            database_pool=MagicMock(),
            cache=MagicMock(),
        )
        service._provision_engagement_access = AsyncMock()

        invitation = SimpleNamespace(
            scope=InviteScope.WORKSPACE,
            org_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            workspace_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            role="viewer",
            grc_role_code="grc_lead_auditor",
            email="auditor@example.com",
            tenant_key="default",
            expires_at="2026-04-05T06:52:43.847164",
            engagement_id=None,
            engagement_ids=[
                "2c21824c-f57c-4f34-aac9-6d61cec9baae",
                "3d31824c-f57c-4f34-aac9-6d61cec9baaf",
            ],
            framework_id=None,
            framework_ids=None,
        )

        conn = SimpleNamespace(
            execute=AsyncMock(),
            fetchval=AsyncMock(return_value=None),
        )

        await service._auto_enroll(
            conn,
            invitation=invitation,
            user_id="22222222-2222-2222-2222-222222222222",
            now="2026-04-02T06:53:16.905122",
        )

        self.assertEqual(service._provision_engagement_access.await_count, 2)
        provisioned_ids = [
            call.kwargs["engagement_id"]
            for call in service._provision_engagement_access.await_args_list
        ]
        self.assertEqual(
            provisioned_ids,
            [
                "2c21824c-f57c-4f34-aac9-6d61cec9baae",
                "3d31824c-f57c-4f34-aac9-6d61cec9baaf",
            ],
        )


if __name__ == "__main__":
    unittest.main()
