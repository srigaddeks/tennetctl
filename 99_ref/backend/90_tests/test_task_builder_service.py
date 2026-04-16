from __future__ import annotations

import json
from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.20_ai.31_task_builder.service")
schemas_module = import_module("backend.20_ai.31_task_builder.schemas")

TaskBuilderService = service_module.TaskBuilderService
GeneratedTask = schemas_module.GeneratedTask
TaskGroupResponse = schemas_module.TaskGroupResponse


class _AcquireContext:
    def __init__(self, connection) -> None:
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _TransactionContext(_AcquireContext):
    pass


class _FakePool:
    def __init__(self, connection) -> None:
        self._connection = connection

    def acquire(self):
        return _AcquireContext(self._connection)

    def transaction(self):
        return _TransactionContext(self._connection)


class TaskBuilderServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.connection = MagicMock()
        self.connection.execute = AsyncMock()
        self.pool = _FakePool(self.connection)
        self.cache = SimpleNamespace(delete_pattern=AsyncMock())
        self.service = TaskBuilderService(
            settings=MagicMock(ai_max_tokens=4000),
            database_pool=self.pool,
            cache=self.cache,
        )
        self.service._logger = MagicMock()
        self.service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        self.service._task_repository = SimpleNamespace(
            create_task=AsyncMock(),
            set_task_property=AsyncMock(),
        )
        self.service._event_repository = SimpleNamespace(create_event=AsyncMock())
        self.service._resolve_llm = AsyncMock(return_value=("http://llm", "key", "model"))

    async def test_preview_filters_malformed_and_duplicate_tasks(self) -> None:
        self.service._repository = SimpleNamespace(
            get_framework=AsyncMock(return_value={"framework_code": "SOC2", "name": "SOC 2"}),
            list_controls=AsyncMock(
                return_value=[
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "control_code": "CC6.1",
                        "control_type": "preventive",
                        "criticality_code": "high",
                        "automation_potential": "partial",
                        "name": "Review MFA configuration",
                        "description": "Validate MFA enforcement",
                        "implementation_guidance": "Use your IdP export",
                        "test_count": 1,
                        "passing_execution_count": 1,
                        "failing_execution_count": 0,
                        "latest_execution_at": "2026-03-30T10:00:00",
                        "latest_result_statuses": "pass",
                        "evidence_summaries": "Okta export attached",
                    }
                ]
            ),
            list_existing_non_terminal_tasks=AsyncMock(
                return_value=[
                    {
                        "control_id": "11111111-1111-1111-1111-111111111111",
                        "task_type_code": "evidence_collection",
                        "status_code": "open",
                        "title": "Export MFA configuration from Okta",
                        "acceptance_criteria": "Upload the export showing MFA is enforced for all admins.",
                    }
                ]
            ),
        )

        llm_payload = [
            {
                "control_id": "11111111-1111-1111-1111-111111111111",
                "control_code": "CC6.1",
                "tasks": [
                    {
                        "title": "Export MFA configuration from Okta",
                        "description": "Collect the current IdP export.",
                        "priority_code": "high",
                        "due_days_from_now": 14,
                        "acceptance_criteria": "Upload the export showing MFA is enforced for all admins.",
                        "task_type_code": "evidence_collection",
                    },
                    {
                        "title": "Enable MFA for legacy admin accounts",
                        "description": "Close the remaining MFA gap for legacy admin users.",
                        "priority_code": "critical",
                        "due_days_from_now": 9,
                        "acceptance_criteria": "All legacy admin accounts are covered by MFA and verified in Okta.",
                        "task_type_code": "control_remediation",
                        "remediation_plan": "1. Identify legacy admins. 2. Enforce MFA. 3. Validate coverage.",
                    },
                    {
                        "title": "",
                        "description": "bad row",
                        "priority_code": "medium",
                        "due_days_from_now": 30,
                        "acceptance_criteria": "",
                        "task_type_code": "evidence_collection",
                    },
                ],
            }
        ]

        with (
            patch.object(service_module, "require_permission", AsyncMock()),
            patch.object(service_module, "llm_complete", AsyncMock(return_value=json.dumps(llm_payload))),
        ):
            result = await self.service.preview_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                framework_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                user_context="Focus on MFA readiness.",
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].control_code, "CC6.1")
        self.assertEqual(len(result[0].tasks), 1)
        self.assertEqual(result[0].tasks[0].task_type_code, "control_remediation")
        self.assertEqual(result[0].tasks[0].due_days_from_now, 7)

    async def test_apply_is_idempotent_for_replayed_payload(self) -> None:
        existing_tasks: list[dict] = []

        async def list_existing_non_terminal_tasks(connection, *, tenant_key: str, control_ids: list[str]) -> list[dict]:
            return [task for task in existing_tasks if task["control_id"] in control_ids]

        self.service._repository = SimpleNamespace(
            list_existing_non_terminal_tasks=AsyncMock(side_effect=list_existing_non_terminal_tasks),
        )

        async def create_task_side_effect(connection, **kwargs):
            existing_tasks.append(
                {
                    "control_id": kwargs["entity_id"],
                    "task_type_code": kwargs["task_type_code"],
                    "title": "Collect Okta MFA evidence",
                    "acceptance_criteria": "Upload an export proving MFA is enabled for administrators.",
                    "is_terminal": False,
                }
            )
            return None

        self.service._task_repository = SimpleNamespace(
            create_task=AsyncMock(side_effect=create_task_side_effect),
            set_task_property=AsyncMock(),
        )

        task_groups = [
            TaskGroupResponse(
                control_id="11111111-1111-1111-1111-111111111111",
                control_code="CC6.1",
                tasks=[
                    GeneratedTask(
                        title="Collect Okta MFA evidence",
                        description="Export Okta admin MFA settings for audit evidence.",
                        priority_code="high",
                        due_days_from_now=14,
                        acceptance_criteria="Upload an export proving MFA is enabled for administrators.",
                        task_type_code="evidence_collection",
                    )
                ],
            )
        ]

        with patch.object(service_module, "require_permission", AsyncMock()):
            first = await self.service.apply_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                framework_id="framework-1",
                task_groups=task_groups,
            )
            second = await self.service.apply_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                framework_id="framework-1",
                task_groups=task_groups,
            )

        self.assertEqual((first.created, first.skipped), (1, 0))
        self.assertEqual((second.created, second.skipped), (0, 1))

    async def test_apply_skips_duplicate_created_after_preview(self) -> None:
        task_groups = [
            TaskGroupResponse(
                control_id="11111111-1111-1111-1111-111111111111",
                control_code="CC6.1",
                tasks=[
                    GeneratedTask(
                        title="Collect access review evidence",
                        description="Upload the quarterly access review report.",
                        priority_code="medium",
                        due_days_from_now=30,
                        acceptance_criteria="Quarterly access review report is attached and approved.",
                        task_type_code="evidence_collection",
                    )
                ],
            )
        ]

        self.service._repository = SimpleNamespace(
            list_existing_non_terminal_tasks=AsyncMock(
                return_value=[
                    {
                        "control_id": "11111111-1111-1111-1111-111111111111",
                        "task_type_code": "evidence_collection",
                        "title": "Collect access review evidence",
                        "acceptance_criteria": "Quarterly access review report is attached and approved.",
                        "is_terminal": False,
                    }
                ]
            )
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            result = await self.service.apply_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                framework_id="framework-1",
                task_groups=task_groups,
            )

        self.assertEqual((result.created, result.skipped), (0, 1))
        self.service._task_repository.create_task.assert_not_awaited()

    async def test_preview_then_apply_integration_path(self) -> None:
        created_state: list[dict] = []

        async def list_existing_non_terminal_tasks(connection, *, tenant_key: str, control_ids: list[str]) -> list[dict]:
            return [task for task in created_state if task["control_id"] in control_ids]

        repository = SimpleNamespace(
            get_framework=AsyncMock(return_value={"framework_code": "SOC2", "name": "SOC 2"}),
            list_controls=AsyncMock(
                return_value=[
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "control_code": "CC7.2",
                        "control_type": "detective",
                        "criticality_code": "medium",
                        "automation_potential": "manual",
                        "name": "Review incident logs",
                        "description": "Review incident logs quarterly",
                        "implementation_guidance": "Use SIEM reports",
                        "test_count": 1,
                        "passing_execution_count": 0,
                        "failing_execution_count": 0,
                        "latest_execution_at": None,
                        "latest_result_statuses": None,
                        "evidence_summaries": None,
                    }
                ]
            ),
            list_existing_non_terminal_tasks=AsyncMock(side_effect=list_existing_non_terminal_tasks),
        )
        self.service._repository = repository

        async def create_task_side_effect(connection, **kwargs):
            created_state.append(
                {
                    "control_id": kwargs["entity_id"],
                    "task_type_code": kwargs["task_type_code"],
                    "title": "Upload quarterly incident log review evidence",
                    "acceptance_criteria": "Quarterly SIEM review report is uploaded and dated.",
                    "is_terminal": False,
                }
            )
            return None

        self.service._task_repository = SimpleNamespace(
            create_task=AsyncMock(side_effect=create_task_side_effect),
            set_task_property=AsyncMock(),
        )

        llm_payload = [
            {
                "control_id": "11111111-1111-1111-1111-111111111111",
                "control_code": "CC7.2",
                "tasks": [
                    {
                        "title": "Upload quarterly incident log review evidence",
                        "description": "Collect the signed SIEM review output for the quarter.",
                        "priority_code": "medium",
                        "due_days_from_now": 30,
                        "acceptance_criteria": "Quarterly SIEM review report is uploaded and dated.",
                        "task_type_code": "evidence_collection",
                    }
                ],
            }
        ]

        with (
            patch.object(service_module, "require_permission", AsyncMock()),
            patch.object(service_module, "llm_complete", AsyncMock(return_value=json.dumps(llm_payload))),
        ):
            preview = await self.service.preview_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                framework_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                user_context="Prepare for audit evidence collection.",
            )
            apply_result = await self.service.apply_tasks(
                user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                tenant_key="tenant-1",
                org_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                workspace_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                framework_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                task_groups=preview,
            )

        self.assertEqual(len(preview), 1)
        self.assertEqual(preview[0].tasks[0].task_type_code, "evidence_collection")
        self.assertEqual((apply_result.created, apply_result.skipped), (1, 0))


class TaskBuilderDuplicateMatcherTests(unittest.TestCase):
    def test_terminal_tasks_do_not_block_duplicates(self) -> None:
        candidate = GeneratedTask(
            title="Collect Okta MFA evidence",
            description="Collect current export.",
            priority_code="medium",
            due_days_from_now=30,
            acceptance_criteria="Upload proof that MFA is enabled for admins.",
            task_type_code="evidence_collection",
        )
        existing = {
            "task_type_code": "evidence_collection",
            "title": "Collect Okta MFA evidence",
            "acceptance_criteria": "Upload proof that MFA is enabled for admins.",
            "is_terminal": True,
        }
        self.assertFalse(service_module._is_duplicate_task(candidate, existing))
