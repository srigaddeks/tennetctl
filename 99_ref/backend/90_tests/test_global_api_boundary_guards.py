from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


attachments_router_module = import_module("backend.09_attachments.01_attachments.router")
tasks_service_module = import_module("backend.07_tasks.02_tasks.service")
task_models_module = import_module("backend.07_tasks.02_tasks.models")

AttachmentAuthorizationError = attachments_router_module.AuthorizationError
TaskAuthorizationError = tasks_service_module.AuthorizationError
TaskService = tasks_service_module.TaskService
TaskRecord = task_models_module.TaskRecord


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


class GlobalApiBoundaryGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_attachment_boundary_denies_org_user_without_engagement_access(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        attachment_service = SimpleNamespace(
            _repository=SimpleNamespace(
                get_attachment_by_id=AsyncMock(
                    return_value=SimpleNamespace(auditor_access=False),
                ),
                list_attachment_engagement_contexts=AsyncMock(
                    return_value=[{"engagement_id": "eng-1"}],
                ),
                has_active_evidence_grant=AsyncMock(return_value=False),
            ),
        )
        engagement_service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_engagement=AsyncMock(return_value=SimpleNamespace(org_id="org-1")),
            get_active_membership_access=AsyncMock(return_value=None),
            validate_auditor_access_and_get_tenant=AsyncMock(return_value=None),
        )

        with patch.object(attachments_router_module, "_get_engagement_service", return_value=engagement_service), patch.object(
            attachments_router_module, "require_permission", AsyncMock()
        ), patch.object(
            attachments_router_module, "check_engagement_access", AsyncMock(return_value=False)
        ), patch.object(
            attachments_router_module, "_get_user_email", AsyncMock(return_value=None)
        ):
            with self.assertRaises(AttachmentAuthorizationError):
                await attachments_router_module._assert_attachment_engagement_boundary(
                    MagicMock(),
                    attachment_service,
                    "att-1",
                    claims,
                )

        attachment_service._repository.has_active_evidence_grant.assert_not_awaited()
        engagement_service.get_active_membership_access.assert_awaited_once()

    async def test_task_detail_denies_org_user_without_engagement_access(self) -> None:
        connection = MagicMock()
        service = TaskService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(
                get=AsyncMock(return_value=None),
                set=AsyncMock(),
                delete=AsyncMock(),
                delete_pattern=AsyncMock(),
            ),
        )
        service._repository = SimpleNamespace(
            get_task_by_id=AsyncMock(
                return_value=TaskRecord(
                    id="task-1",
                    tenant_key="tenant-1",
                    org_id="org-1",
                    workspace_id="workspace-1",
                    task_type_code="evidence_request",
                    priority_code="medium",
                    status_code="open",
                    entity_type="control",
                    entity_id="ctrl-1",
                    assignee_user_id=None,
                    reporter_user_id="reporter-1",
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
            ),
            list_linked_engagement_ids_for_task_target=AsyncMock(return_value=["eng-1"]),
            get_task_detail=AsyncMock(),
        )
        service._engagement_repository = SimpleNamespace(
            get_active_membership_access=AsyncMock(return_value=None),
        )

        with patch.object(tasks_service_module, "require_permission", AsyncMock()), patch.object(
            tasks_service_module, "check_engagement_access", AsyncMock(return_value=False)
        ):
            with self.assertRaises(TaskAuthorizationError):
                await service.get_task(
                    user_id="user-1",
                    task_id="task-1",
                )

        service._repository.get_task_detail.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
