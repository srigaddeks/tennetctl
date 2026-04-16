from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.07_tasks.02_tasks.service")
models_module = import_module("backend.07_tasks.02_tasks.models")
schemas_module = import_module("backend.07_tasks.02_tasks.schemas")

TaskService = service_module.TaskService
AuthorizationError = service_module.AuthorizationError
TaskRecord = models_module.TaskRecord
UpdateTaskRequest = schemas_module.UpdateTaskRequest


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


class TaskServiceEngagementGuardTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.connection = MagicMock()
        self.pool = _FakePool(self.connection)
        self.cache = SimpleNamespace(
            get=AsyncMock(return_value=None),
            set=AsyncMock(),
            delete=AsyncMock(),
            delete_pattern=AsyncMock(),
        )
        self.service = TaskService(
            settings=MagicMock(),
            database_pool=self.pool,
            cache=self.cache,
        )
        self.service._logger = MagicMock()
        self.service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        self.service._event_repository = SimpleNamespace(create_event=AsyncMock())
        self.service._engagement_repository = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_active_membership_access=AsyncMock(return_value={"membership_type_code": "external_auditor"}),
            list_accessible_engagement_ids_for_user=AsyncMock(return_value=["eng-1", "eng-2"]),
        )
        self.service._repository = SimpleNamespace(
            list_linked_engagement_ids_for_task_target=AsyncMock(return_value=["eng-1"]),
            get_task_by_id=AsyncMock(),
            update_task=AsyncMock(),
            is_terminal_status=AsyncMock(return_value=False),
            get_task_detail=AsyncMock(),
            list_tasks=AsyncMock(return_value=([], 0)),
            get_task_summary=AsyncMock(
                return_value={
                    "open_count": 0,
                    "in_progress_count": 0,
                    "pending_verification_count": 0,
                    "resolved_count": 0,
                    "cancelled_count": 0,
                    "overdue_count": 0,
                    "resolved_this_week_count": 0,
                    "by_type": [],
                }
            ),
            soft_delete_task=AsyncMock(return_value=True),
        )

    def _make_task_record(self, *, reporter_user_id: str, assignee_user_id: str | None = None) -> TaskRecord:
        return TaskRecord(
            id="task-1",
            tenant_key="tenant-1",
            org_id="org-1",
            workspace_id="workspace-1",
            task_type_code="evidence_request",
            priority_code="medium",
            status_code="open",
            entity_type="engagement",
            entity_id="eng-1",
            assignee_user_id=assignee_user_id,
            reporter_user_id=reporter_user_id,
            due_date=None,
            start_date=None,
            completed_at=None,
            estimated_hours=None,
            actual_hours=None,
            is_active=True,
            version=1,
            created_at="2026-04-01T00:00:00Z",
            updated_at="2026-04-01T00:00:00Z",
        )

    async def test_update_task_blocks_assignee_from_reassigning_engagement_task(self) -> None:
        self.service._repository.get_task_by_id.return_value = self._make_task_record(
            reporter_user_id="reporter-1",
            assignee_user_id="member-1",
        )

        with patch.object(service_module, "require_permission", AsyncMock()), patch.object(
            service_module, "check_engagement_access", AsyncMock(return_value=False)
        ):
            with self.assertRaises(AuthorizationError):
                await self.service.update_task(
                    user_id="member-1",
                    task_id="task-1",
                    request=UpdateTaskRequest(assignee_user_id="other-user"),
                )

        self.service._repository.update_task.assert_not_awaited()

    async def test_delete_task_blocks_plain_engagement_member(self) -> None:
        self.service._repository.get_task_by_id.return_value = self._make_task_record(
            reporter_user_id="reporter-1",
            assignee_user_id="member-1",
        )

        with patch.object(service_module, "require_permission", AsyncMock()), patch.object(
            service_module, "check_engagement_access", AsyncMock(return_value=False)
        ):
            with self.assertRaises(AuthorizationError):
                await self.service.delete_task(
                    user_id="member-1",
                    task_id="task-1",
                )

        self.service._repository.soft_delete_task.assert_not_awaited()

    async def test_list_tasks_prevalidated_passes_accessible_engagement_ids_to_repository(self) -> None:
        result = await self.service.list_tasks_prevalidated(
            user_id="user-1",
            tenant_key="tenant-1",
            org_id="org-1",
            workspace_id="workspace-1",
        )

        self.assertEqual(result.total, 0)
        self.service._engagement_repository.list_accessible_engagement_ids_for_user.assert_awaited_once()
        self.service._repository.list_tasks.assert_awaited_once()
        kwargs = self.service._repository.list_tasks.await_args.kwargs
        self.assertEqual(kwargs["accessible_engagement_ids"], ["eng-1", "eng-2"])

    async def test_get_task_summary_passes_accessible_engagement_ids_to_repository(self) -> None:
        with patch.object(service_module, "require_permission", AsyncMock()):
            summary = await self.service.get_task_summary(
                user_id="user-1",
                tenant_key="tenant-1",
                org_id="org-1",
                workspace_id="workspace-1",
            )

        self.assertEqual(summary.open_count, 0)
        kwargs = self.service._repository.get_task_summary.await_args.kwargs
        self.assertEqual(kwargs["accessible_engagement_ids"], ["eng-1", "eng-2"])
