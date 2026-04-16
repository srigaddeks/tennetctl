from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


tasks_service_module = import_module("backend.07_tasks.02_tasks.service")
tasks_schemas_module = import_module("backend.07_tasks.02_tasks.schemas")
tasks_models_module = import_module("backend.07_tasks.02_tasks.models")
findings_service_module = import_module("backend.09_assessments._03_findings.service")
findings_schemas_module = import_module("backend.09_assessments.schemas")
findings_models_module = import_module("backend.09_assessments.models")

TaskService = tasks_service_module.TaskService
CreateTaskRequest = tasks_schemas_module.CreateTaskRequest
UpdateTaskRequest = tasks_schemas_module.UpdateTaskRequest
TaskRecord = tasks_models_module.TaskRecord
TaskDetailRecord = tasks_models_module.TaskDetailRecord

FindingService = findings_service_module.FindingService
CreateFindingRequest = findings_schemas_module.CreateFindingRequest
UpdateFindingRequest = findings_schemas_module.UpdateFindingRequest
FindingRecord = findings_models_module.FindingRecord


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


class TaskAndFindingAuditEventTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_task_request_normalizes_blank_optional_entity_fields(self) -> None:
        request = CreateTaskRequest(
            org_id="org-1",
            workspace_id="ws-1",
            task_type_code="evidence_request",
            priority_code="medium",
            entity_type="   ",
            entity_id="   ",
            assignee_user_id="   ",
            title="Review evidence pack",
        )

        self.assertIsNone(request.entity_type)
        self.assertIsNone(request.entity_id)
        self.assertIsNone(request.assignee_user_id)

    async def test_create_task_prevalidated_writes_task_created_audit_event(self) -> None:
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
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            create_task=AsyncMock(),
            set_task_property=AsyncMock(),
            get_task_detail=AsyncMock(
                return_value=TaskDetailRecord(
                    id="task-1",
                    tenant_key="tenant-1",
                    org_id="org-1",
                    workspace_id="ws-1",
                    task_type_code="evidence_request",
                    task_type_name="Evidence Request",
                    priority_code="medium",
                    priority_name="Medium",
                    status_code="open",
                    status_name="Open",
                    is_terminal=False,
                    entity_type="engagement",
                    entity_id="eng-1",
                    assignee_user_id=None,
                    reporter_user_id="user-1",
                    due_date=None,
                    start_date=None,
                    completed_at=None,
                    estimated_hours=None,
                    actual_hours=None,
                    is_active=True,
                    version=1,
                    created_at="2026-04-01T00:00:00Z",
                    updated_at="2026-04-01T00:00:00Z",
                    title="Review evidence pack",
                    description=None,
                    acceptance_criteria=None,
                    resolution_notes=None,
                    remediation_plan=None,
                    co_assignee_count=0,
                    blocker_count=0,
                    comment_count=0,
                )
            ),
        )
        service._event_repository = SimpleNamespace(create_event=AsyncMock())
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        await service.create_task_prevalidated(
            user_id="user-1",
            tenant_key="tenant-1",
            request=CreateTaskRequest(
                org_id="org-1",
                workspace_id="ws-1",
                task_type_code="evidence_request",
                priority_code="medium",
                entity_type="engagement",
                entity_id="eng-1",
                title="Review evidence pack",
            ),
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "task_created")
        self.assertEqual(audit_entry.entity_type, "task")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["title"], "Review evidence pack")

    async def test_update_task_writes_task_updated_audit_event(self) -> None:
        connection = MagicMock()
        existing = TaskRecord(
            id="task-1",
            tenant_key="tenant-1",
            org_id="org-1",
            workspace_id="ws-1",
            task_type_code="evidence_request",
            priority_code="medium",
            status_code="open",
            entity_type="engagement",
            entity_id="eng-1",
            assignee_user_id=None,
            reporter_user_id="user-1",
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
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            get_task_by_id=AsyncMock(return_value=existing),
            update_task=AsyncMock(return_value=existing),
            set_task_property=AsyncMock(),
            is_terminal_status=AsyncMock(return_value=False),
            get_task_detail=AsyncMock(
                return_value=TaskDetailRecord(
                    id="task-1",
                    tenant_key="tenant-1",
                    org_id="org-1",
                    workspace_id="ws-1",
                    task_type_code="evidence_request",
                    task_type_name="Evidence Request",
                    priority_code="medium",
                    priority_name="Medium",
                    status_code="open",
                    status_name="Open",
                    is_terminal=False,
                    entity_type="engagement",
                    entity_id="eng-1",
                    assignee_user_id=None,
                    reporter_user_id="user-1",
                    due_date=None,
                    start_date=None,
                    completed_at=None,
                    estimated_hours=None,
                    actual_hours=None,
                    is_active=True,
                    version=1,
                    created_at="2026-04-01T00:00:00Z",
                    updated_at="2026-04-01T01:00:00Z",
                    title="Updated title",
                    description=None,
                    acceptance_criteria=None,
                    resolution_notes=None,
                    remediation_plan=None,
                    co_assignee_count=0,
                    blocker_count=0,
                    comment_count=0,
                )
            ),
        )
        service._event_repository = SimpleNamespace(create_event=AsyncMock())
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        service._get_task_engagement_lifecycle_role = AsyncMock(return_value="elevated")
        service._require_task_permission = AsyncMock()
        service._assert_task_engagement_boundary = AsyncMock()

        await service.update_task(
            user_id="user-1",
            task_id="task-1",
            request=UpdateTaskRequest(title="Updated title"),
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "task_updated")
        self.assertEqual(audit_entry.entity_type, "task")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["title"], "Updated title")

    async def test_delete_task_writes_task_deleted_audit_event(self) -> None:
        connection = MagicMock()
        existing = TaskRecord(
            id="task-1",
            tenant_key="tenant-1",
            org_id="org-1",
            workspace_id="ws-1",
            task_type_code="evidence_request",
            priority_code="medium",
            status_code="open",
            entity_type="engagement",
            entity_id="eng-1",
            assignee_user_id=None,
            reporter_user_id="user-1",
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
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            get_task_by_id=AsyncMock(return_value=existing),
            soft_delete_task=AsyncMock(return_value=True),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        service._get_task_engagement_lifecycle_role = AsyncMock(return_value="elevated")
        service._require_task_permission = AsyncMock()
        service._assert_task_engagement_boundary = AsyncMock()

        await service.delete_task(
            user_id="user-1",
            task_id="task-1",
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "task_deleted")
        self.assertEqual(audit_entry.entity_type, "task")
        self.assertEqual(audit_entry.actor_id, "user-1")

    async def test_create_finding_prevalidated_writes_finding_created_audit_event(self) -> None:
        connection = MagicMock()
        service = FindingService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(
                get=AsyncMock(return_value=None),
                set=AsyncMock(),
                delete=AsyncMock(),
                delete_pattern=AsyncMock(),
            ),
        )
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            check_assessment_locked=AsyncMock(return_value=False),
            create_finding=AsyncMock(
                return_value=FindingRecord(
                    id="finding-1",
                    assessment_id="assessment-1",
                    control_id="ctrl-1",
                    risk_id=None,
                    severity_code="medium",
                    finding_type="observation",
                    finding_status_code="open",
                    assigned_to=None,
                    remediation_due_date=None,
                    severity_name="Medium",
                    finding_status_name="Open",
                    title="Missing evidence trail",
                    description="Sampling evidence was incomplete.",
                    recommendation=None,
                    is_active=True,
                    created_at="2026-04-01T00:00:00Z",
                    updated_at="2026-04-01T00:00:00Z",
                    created_by="user-1",
                )
            ),
            upsert_finding_property=AsyncMock(),
            get_finding_by_id=AsyncMock(return_value=None),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        await service.create_finding_prevalidated(
            user_id="user-1",
            assessment_id="assessment-1",
            request=CreateFindingRequest(
                control_id="ctrl-1",
                severity_code="medium",
                finding_type="observation",
                title="Missing evidence trail",
                description="Sampling evidence was incomplete.",
            ),
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "finding_created")
        self.assertEqual(audit_entry.entity_type, "finding")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["assessment_id"], "assessment-1")

    async def test_update_finding_prevalidated_writes_finding_updated_audit_event(self) -> None:
        connection = MagicMock()
        existing = FindingRecord(
            id="finding-1",
            assessment_id="assessment-1",
            control_id="ctrl-1",
            risk_id=None,
            severity_code="medium",
            finding_type="observation",
            finding_status_code="open",
            assigned_to=None,
            remediation_due_date=None,
            severity_name="Medium",
            finding_status_name="Open",
            title="Missing evidence trail",
            description="Sampling evidence was incomplete.",
            recommendation=None,
            is_active=True,
            created_at="2026-04-01T00:00:00Z",
            updated_at="2026-04-01T00:00:00Z",
            created_by="user-1",
        )
        updated = FindingRecord(
            **{**existing.__dict__, "title": "Updated title", "updated_at": "2026-04-01T01:00:00Z"}
        )
        service = FindingService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(
                get=AsyncMock(return_value=None),
                set=AsyncMock(),
                delete=AsyncMock(),
                delete_pattern=AsyncMock(),
            ),
        )
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            get_finding_by_id=AsyncMock(side_effect=[existing, updated]),
            update_finding=AsyncMock(),
            upsert_finding_property=AsyncMock(),
            check_assessment_locked=AsyncMock(return_value=False),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        await service.update_finding_prevalidated(
            user_id="user-1",
            finding_id="finding-1",
            request=UpdateFindingRequest(title="Updated title"),
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "finding_updated")
        self.assertEqual(audit_entry.entity_type, "finding")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["assessment_id"], "assessment-1")

    async def test_delete_finding_prevalidated_writes_finding_deleted_audit_event(self) -> None:
        connection = MagicMock()
        existing = FindingRecord(
            id="finding-1",
            assessment_id="assessment-1",
            control_id="ctrl-1",
            risk_id=None,
            severity_code="medium",
            finding_type="observation",
            finding_status_code="open",
            assigned_to=None,
            remediation_due_date=None,
            severity_name="Medium",
            finding_status_name="Open",
            title="Missing evidence trail",
            description="Sampling evidence was incomplete.",
            recommendation=None,
            is_active=True,
            created_at="2026-04-01T00:00:00Z",
            updated_at="2026-04-01T00:00:00Z",
            created_by="user-1",
        )
        service = FindingService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(
                get=AsyncMock(return_value=None),
                set=AsyncMock(),
                delete=AsyncMock(),
                delete_pattern=AsyncMock(),
            ),
        )
        service._engagement_repository = SimpleNamespace(is_user_globally_active=AsyncMock(return_value=True))
        service._repository = SimpleNamespace(
            get_finding_by_id=AsyncMock(return_value=existing),
            soft_delete_finding=AsyncMock(return_value=True),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        await service.delete_finding_prevalidated(
            user_id="user-1",
            finding_id="finding-1",
        )

        service._audit_writer.write_entry.assert_awaited_once()
        audit_entry = service._audit_writer.write_entry.await_args.args[1]
        self.assertEqual(audit_entry.event_type, "finding_deleted")
        self.assertEqual(audit_entry.entity_type, "finding")
        self.assertEqual(audit_entry.actor_id, "user-1")
        self.assertEqual(audit_entry.properties["assessment_id"], "assessment-1")


if __name__ == "__main__":
    unittest.main()
