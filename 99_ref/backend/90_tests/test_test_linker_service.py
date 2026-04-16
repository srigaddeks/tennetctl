from __future__ import annotations

from importlib import import_module
import unittest
from unittest.mock import AsyncMock


service_module = import_module("backend.20_ai.30_test_linker.service")
schemas_module = import_module("backend.20_ai.30_test_linker.schemas")

ImportedTestLinkerService = service_module.TestLinkerService
ValidationError = service_module.ValidationError
BulkLinkRequest = schemas_module.BulkLinkRequest
ListPendingMappingsQuery = schemas_module.ListPendingMappingsQuery


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


class TestLinkerServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.connection = AsyncMock()
        self.pool = _FakePool(self.connection)
        self.service = ImportedTestLinkerService(settings=type("Settings", (), {"ai_max_tokens": 4096})(), database_pool=self.pool)
        self.service._repo = AsyncMock()
        service_module.require_permission = AsyncMock()

    async def test_enqueue_bulk_link_rejects_empty_control_scope(self) -> None:
        self.service._repo.list_all_controls = AsyncMock(return_value=[])
        self.service._repo.list_tests = AsyncMock(return_value=[{"id": "test-1"}])

        with self.assertRaises(ValidationError):
            await self.service.enqueue_bulk_link(
                user_id="user-1",
                tenant_key="tenant-1",
                request=BulkLinkRequest(org_id="org-1"),
            )

    async def test_enqueue_bulk_link_returns_job_metadata(self) -> None:
        self.service._repo.list_all_controls = AsyncMock(return_value=[{"id": "control-1"}, {"id": "control-2"}])
        self.service._repo.list_tests = AsyncMock(return_value=[{"id": "test-1"}])
        self.service._enqueue_job = AsyncMock(return_value="job-123")

        result = await self.service.enqueue_bulk_link(
            user_id="user-1",
            tenant_key="tenant-1",
            request=BulkLinkRequest(
                org_id="org-1",
                workspace_id="ws-1",
                framework_id="fw-1",
                test_ids=["test-1"],
                control_ids=["control-1"],
                dry_run=True,
            ),
        )

        self.assertEqual(result.job_id, "job-123")
        self.assertEqual(result.control_count, 2)
        self.assertEqual(result.test_count, 1)
        self.assertTrue(result.dry_run)
        self.service._enqueue_job.assert_awaited_once()

    async def test_list_pending_uses_current_user_for_mine_only_queries(self) -> None:
        self.service._repo.list_pending_mappings = AsyncMock(return_value=([{
            "id": "mapping-1",
            "control_test_id": "test-1",
            "control_id": "control-1",
            "link_type": "covers",
            "ai_confidence": 0.9,
            "ai_rationale": "Good match",
            "approval_status": "pending",
            "created_at": "2026-03-30T00:00:00",
            "created_by": "user-1",
            "test_name": "Test",
            "test_code": "T-1",
            "control_name": "Control",
            "control_code": "C-1",
            "framework_id": "fw-1",
            "framework_code": "FW-1",
        }], 1))

        response = await self.service.list_pending(
            user_id="user-1",
            tenant_key="tenant-1",
            query=ListPendingMappingsQuery(org_id="org-1", mine_only=True),
        )

        self.assertEqual(response.total, 1)
        self.service._repo.list_pending_mappings.assert_awaited_once()
        kwargs = self.service._repo.list_pending_mappings.await_args.kwargs
        self.assertEqual(kwargs["created_by"], "user-1")
