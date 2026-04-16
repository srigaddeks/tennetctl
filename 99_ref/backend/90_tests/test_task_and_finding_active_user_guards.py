from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


tasks_service_module = import_module("backend.07_tasks.02_tasks.service")
findings_service_module = import_module("backend.09_assessments._03_findings.service")

TaskService = tasks_service_module.TaskService
FindingService = findings_service_module.FindingService
TaskAuthorizationError = tasks_service_module.AuthorizationError
FindingAuthorizationError = findings_service_module.AuthorizationError


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


class TaskAndFindingActiveUserGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_task_summary_blocks_inactive_user(self) -> None:
        connection = MagicMock()
        service = TaskService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock()),
        )
        service._engagement_repository = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
            list_accessible_engagement_ids_for_user=AsyncMock(),
        )
        service._repository = SimpleNamespace(get_task_summary=AsyncMock())

        with patch.object(tasks_service_module, "require_permission", AsyncMock()):
            with self.assertRaises(TaskAuthorizationError) as exc_info:
                await service.get_task_summary(
                    user_id="user-1",
                    tenant_key="tenant-1",
                    org_id="org-1",
                    workspace_id="ws-1",
                )

        self.assertIn("inactive or suspended", str(exc_info.exception))
        service._repository.get_task_summary.assert_not_awaited()

    async def test_findings_list_blocks_inactive_user(self) -> None:
        connection = MagicMock()
        service = FindingService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock()),
        )
        service._engagement_repository = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
        )
        service._repository = SimpleNamespace(list_findings=AsyncMock())

        with patch.object(findings_service_module, "require_permission", AsyncMock()):
            with self.assertRaises(FindingAuthorizationError) as exc_info:
                await service.list_findings(
                    user_id="user-1",
                    assessment_id="assessment-1",
                )

        self.assertIn("inactive or suspended", str(exc_info.exception))
        service._repository.list_findings.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
