from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.03_auth_manage.11_admin.service")

AdminService = service_module.AdminService


class _AcquireContext:
    def __init__(self, connection) -> None:
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakePool:
    def __init__(self, connection) -> None:
        self._connection = connection

    def acquire(self):
        return _AcquireContext(self._connection)

    def transaction(self):
        return _AcquireContext(self._connection)


class AdminUserDisableInvalidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_disable_user_revokes_sessions_memberships_and_grants(self) -> None:
        connection = MagicMock()
        service = AdminService(
            settings=MagicMock(default_tenant_key="default"),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(),
        )
        service._repository = SimpleNamespace(
            set_user_disabled=AsyncMock(return_value=True),
            revoke_all_user_sessions=AsyncMock(return_value=2),
        )
        service._engagement_repository = SimpleNamespace(
            deactivate_memberships_for_user=AsyncMock(return_value=3),
            revoke_evidence_grants_for_user=AsyncMock(return_value=4),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        actor_id = "00000000-0000-0000-0000-000000000001"
        user_id = "00000000-0000-0000-0000-000000000002"

        with patch.object(service_module, "require_permission", AsyncMock()):
            result = await service.disable_user(
                actor_id=actor_id,
                user_id=user_id,
                client_ip="127.0.0.1",
                request_id="req-1",
            )

        self.assertTrue(result.is_disabled)
        service._repository.revoke_all_user_sessions.assert_awaited_once()
        service._engagement_repository.deactivate_memberships_for_user.assert_awaited_once()
        service._engagement_repository.revoke_evidence_grants_for_user.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.properties["revoked_session_count"], "2")
        self.assertEqual(audit_entry.properties["revoked_membership_count"], "3")
        self.assertEqual(audit_entry.properties["revoked_evidence_grant_count"], "4")


if __name__ == "__main__":
    unittest.main()
