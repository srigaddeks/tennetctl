from __future__ import annotations

import json
import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.10_sandbox.04_signals.service")

SignalService = service_module.SignalService
ValidationError = service_module.ValidationError
ConflictError = service_module.ConflictError
extract_test_cases = service_module._extract_test_cases
augment_live_dataset_shape = service_module._augment_live_dataset_shape


class UndefinedTableError(Exception):
    pass


class UndefinedColumnError(Exception):
    pass


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

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)

    def transaction(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


class _FakeRepository:
    def __init__(self, properties: dict[str, str] | None = None) -> None:
        self._properties = properties or {}
        self._record = SimpleNamespace(
            id="signal-1",
            tenant_key="default",
            org_id="org-1",
            workspace_id=None,
            signal_code="github_workflow_security_integrity",
            version_number=1,
            signal_status_code="draft",
            signal_status_name="Draft",
            python_hash=None,
            timeout_ms=1000,
            max_memory_mb=128,
            is_active=True,
            created_at="2026-03-24T00:00:00+00:00",
            updated_at="2026-03-24T00:00:00+00:00",
            name="github_workflow_security_integrity",
            description="Test signal",
            python_source=self._properties.get("python_source"),
            source_prompt=None,
            caep_event_type=None,
            risc_event_type=None,
        )

    async def get_signal_by_id(self, _conn, _signal_id: str):
        return self._record

    async def get_signal_properties(self, _conn, _signal_id: str) -> dict[str, str]:
        return self._properties

    async def get_next_version(self, _conn, _org_id: str, _signal_code: str) -> int:
        return 1

    async def update_signal_status(self, _conn, _signal_id: str, new_status: str, **_kwargs) -> None:
        self._record.signal_status_code = new_status
        self._record.signal_status_name = new_status.title()


def _make_valid_test_case() -> dict:
    return {
        "case_id": "tc_001",
        "scenario_name": "valid case",
        "dataset_input": {"repositories": [{"name": "demo"}]},
        "expected_output": {"result": "pass", "summary": "All good"},
    }


class SignalTestSuiteServiceTests(unittest.IsolatedAsyncioTestCase):
    def _make_service(
        self,
        *,
        connection,
        properties: dict[str, str] | None = None,
    ) -> SignalService:
        service = SignalService(
            settings=MagicMock(
                sandbox_execution_timeout_ms=1000,
                sandbox_execution_max_memory_mb=128,
            ),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(delete=AsyncMock()),
        )
        service._repository = _FakeRepository(properties=properties)
        service._logger = MagicMock()
        return service

    def test_extract_test_cases_filters_out_raw_dataset_records(self) -> None:
        cases = extract_test_cases(
            json.dumps(
                [
                    _make_valid_test_case(),
                    {"repository": "demo-repo", "workflow_count": 3},
                ]
            )
        )

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["case_id"], "tc_001")

    def test_augment_live_dataset_shape_groups_github_workflows_into_repositories(self) -> None:
        dataset = augment_live_dataset_shape(
            {
                "github_repo": [
                    {
                        "name": "kcontrol",
                        "owner_login": "kreesalis",
                        "visibility": "private",
                    }
                ],
                "github_workflow": [
                    {
                        "name": "CI",
                        "repository_full_name": "kreesalis/kcontrol",
                        "path": ".github/workflows/ci.yml",
                        "state": "active",
                        "updated_at": "2026-03-24T10:30:00+05:30",
                    },
                    {
                        "name": "Release",
                        "_external_id": "kreesalis/kcontrol/Release",
                        "path": ".github/workflows/release.yml",
                        "state": "disabled",
                    },
                ],
            }
        )

        repositories = dataset["repositories"]
        workflows = dataset["workflows"]
        self.assertEqual(len(repositories), 1)
        self.assertEqual(repositories[0]["name"], "kreesalis/kcontrol")
        self.assertEqual(len(repositories[0]["workflows"]), 2)
        self.assertTrue(repositories[0]["workflows"][0]["enabled"])
        self.assertFalse(repositories[0]["workflows"][1]["enabled"])
        self.assertEqual(len(workflows), 2)
        self.assertEqual(workflows[0]["repository"], "kreesalis/kcontrol")
        self.assertTrue(workflows[0]["active"])
        self.assertFalse(workflows[1]["active"])
        self.assertEqual(workflows[0]["updated_at"], "2026-03-24T05:00:00")

    async def test_fetch_dataset_case_rows_falls_back_to_legacy_payload_column(self) -> None:
        connection = MagicMock()
        connection.fetch = AsyncMock(
            side_effect=[
                UndefinedTableError('relation "43_dtl_dataset_records" does not exist'),
                UndefinedColumnError('column "payload_data" does not exist'),
                [{"payload": json.dumps(_make_valid_test_case())}],
            ]
        )
        service = self._make_service(connection=connection)

        rows = await service._fetch_dataset_case_rows(connection, test_dataset_id="dataset-1")

        self.assertEqual(len(rows), 1)
        self.assertEqual(connection.fetch.await_count, 3)

    async def test_run_test_suite_override_ignores_default_bundle_and_rejects_raw_dataset(self) -> None:
        bundled_cases = json.dumps([_make_valid_test_case()])
        connection = MagicMock()
        connection.fetchrow = AsyncMock(
            return_value={
                "id": "dataset-1",
                "org_id": "org-1",
                "workspace_id": None,
                "dataset_source_code": "github",
            }
        )
        connection.fetch = AsyncMock(
            return_value=[{"payload": json.dumps({"repository": "demo-repo"})}]
        )
        service = self._make_service(
            connection=connection,
            properties={
                "python_source": "def evaluate(dataset): return {'result': 'pass', 'summary': 'ok', 'details': [], 'metadata': {}}",
                "test_bundle_json": bundled_cases,
            },
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with self.assertRaises(ValidationError) as exc_info:
                await service.run_test_suite(
                    user_id="user-1",
                    tenant_key="default",
                    signal_id="signal-1",
                    org_id="org-1",
                    test_dataset_id="dataset-1",
                )

        self.assertIn("not a signal test dataset", str(exc_info.exception))

    async def test_create_signal_rejects_duplicate_signal_code_with_clear_message(self) -> None:
        connection = MagicMock()
        service = self._make_service(connection=connection)
        service._require_sandbox_permission = AsyncMock()
        service._repository.get_next_version = AsyncMock(return_value=2)

        request = service_module.CreateSignalRequest(
            signal_code="mfa_check_dup",
            workspace_id="workspace-1",
            properties={
                "name": "Duplicate Signal",
                "python_source": "def evaluate(dataset): return {'result': 'pass'}",
            },
            timeout_ms=1000,
            max_memory_mb=128,
        )

        with self.assertRaises(ConflictError) as exc_info:
            await service.create_signal(
                user_id="user-1",
                tenant_key="default",
                org_id="org-1",
                request=request,
            )

        self.assertEqual(str(exc_info.exception), "Signal code 'mfa_check_dup' already exists.")

    async def test_validate_signal_requires_passing_test_suite(self) -> None:
        connection = MagicMock()
        service = self._make_service(
            connection=connection,
            properties={"python_source": "def evaluate(dataset): return {'result': 'pass'}"},
        )
        service.run_test_suite = AsyncMock(
            return_value={
                "signal_id": "signal-1",
                "test_dataset_id": "dataset-1",
                "total_cases": 2,
                "passed": 1,
                "failed": 1,
                "errored": 0,
                "pass_rate": 0.5,
                "results": [],
            }
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with self.assertRaises(ValidationError) as exc_info:
                await service.validate_signal(
                    user_id="user-1",
                    tenant_key="default",
                    signal_id="signal-1",
                )

        self.assertIn("must pass completely", str(exc_info.exception))

    async def test_validate_signal_marks_signal_validated_after_passing_suite(self) -> None:
        connection = MagicMock()
        service = self._make_service(
            connection=connection,
            properties={"python_source": "def evaluate(dataset): return {'result': 'pass'}"},
        )
        service.run_test_suite = AsyncMock(
            return_value={
                "signal_id": "signal-1",
                "test_dataset_id": "dataset-1",
                "total_cases": 2,
                "passed": 2,
                "failed": 0,
                "errored": 0,
                "pass_rate": 1.0,
                "results": [],
            }
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with patch.object(service._audit_writer, "write_entry", AsyncMock()):
                with patch.object(service_module, "write_lifecycle_event", AsyncMock()):
                    response = await service.validate_signal(
                        user_id="user-1",
                        tenant_key="default",
                        signal_id="signal-1",
                    )

        self.assertEqual(response.signal_status_code, "validated")
        service.run_test_suite.assert_awaited_once()
