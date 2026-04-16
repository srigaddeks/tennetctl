from __future__ import annotations

import json
import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.10_sandbox.07_execution.service")
repository_module = import_module("backend.10_sandbox.07_execution.repository")
dataset_models_module = import_module("backend.10_sandbox.03_datasets.models")

ExecutionService = service_module.ExecutionService
RunResponse = service_module.RunResponse
ValidationError = service_module.ValidationError
DatasetDataRecord = dataset_models_module.DatasetDataRecord
DatasetRecord = dataset_models_module.DatasetRecord
parse_json = repository_module._parse_json
parse_json_list = repository_module._parse_json_list


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


class ExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
    def _make_service(self, *, connection) -> ExecutionService:
        service = ExecutionService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(delete=AsyncMock()),
            clickhouse=SimpleNamespace(
                insert_signal_result=AsyncMock(),
                insert_threat_evaluation=AsyncMock(),
            ),
        )
        service._logger = MagicMock()
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())
        service._repository = SimpleNamespace(
            insert_run=AsyncMock(),
            insert_threat_evaluation=AsyncMock(),
            insert_policy_execution=AsyncMock(),
        )
        service._signal_repository = SimpleNamespace(
            get_signal_by_id=AsyncMock(
                return_value=SimpleNamespace(
                    id="signal-1",
                    workspace_id=None,
                    signal_code="github_actions_workflow_activity_and_integrity",
                    python_source="def evaluate(dataset): return {'result': 'warning', 'summary': 'ok', 'details': [], 'metadata': {}}",
                    timeout_ms=1000,
                    max_memory_mb=128,
                    name="Signal 1",
                )
            ),
            get_signal_properties=AsyncMock(return_value={}),
        )
        service._dataset_repository = SimpleNamespace(
            get_dataset_by_id=AsyncMock(
                return_value=DatasetRecord(
                    id="dataset-1",
                    tenant_key="default",
                    org_id="org-1",
                    workspace_id=None,
                    connector_instance_id=None,
                    dataset_code="github-1",
                    dataset_source_code="connector_pull",
                    version_number=1,
                    schema_fingerprint=None,
                    row_count=2,
                    byte_size=0,
                    collected_at=None,
                    is_locked=False,
                    is_active=True,
                    created_at="2026-03-24T00:00:00+00:00",
                    updated_at="2026-03-24T00:00:00+00:00",
                    name="Github",
                    description=None,
                    asset_ids=None,
                )
            ),
            list_records=AsyncMock(),
        )
        service._threat_repository = SimpleNamespace(list_threat_types=AsyncMock(return_value=([], 0)))
        service._policy_repository = SimpleNamespace(list_policies=AsyncMock(return_value=([], 0)))
        service._engine = SimpleNamespace(
            execute=AsyncMock(
                return_value=SimpleNamespace(
                    status="completed",
                    result_code="warning",
                    result_summary="workflow issues detected",
                    result_details=[],
                    metadata={},
                    stdout_capture="",
                    error_message=None,
                    execution_time_ms=12,
                )
            )
        )
        return service

    async def test_execute_signal_builds_augmented_dataset_from_dataset_records(self) -> None:
        connection = MagicMock()
        service = self._make_service(connection=connection)
        workflow_record = DatasetDataRecord(
            id="record-1",
            dataset_id="dataset-1",
            record_seq=1,
            record_name="workflow",
            recorded_at="2026-03-24T00:00:00+00:00",
            source_asset_id=None,
            connector_instance_id=None,
            record_data=json.dumps(
                json.dumps(
                    {
                        "_asset_type": "github_workflow",
                        "_asset_id": "wf-1",
                        "_external_id": "kreesalis/kcontrol/CI",
                        "name": "CI",
                        "path": ".github/workflows/ci.yml",
                        "repository_full_name": "kreesalis/kcontrol",
                        "state": "active",
                        "updated_at": "2026-03-24T10:30:00+05:30",
                    }
                )
            ),
            description="",
        )
        repo_record = DatasetDataRecord(
            id="record-2",
            dataset_id="dataset-1",
            record_seq=2,
            record_name="repo",
            recorded_at="2026-03-24T00:00:00+00:00",
            source_asset_id=None,
            connector_instance_id=None,
            record_data=json.dumps(
                json.dumps(
                    {
                        "_asset_type": "github_repo",
                        "_asset_id": "repo-1",
                        "_external_id": "kreesalis/kcontrol",
                        "name": "kcontrol",
                        "full_name": "kreesalis/kcontrol",
                        "owner_login": "kreesalis",
                        "visibility": "private",
                    }
                )
            ),
            description="",
        )
        service._dataset_repository.list_records = AsyncMock(return_value=([workflow_record, repo_record], 2))

        with patch.object(service_module, "require_permission", AsyncMock()):
            response = await service.execute_signal(
                user_id="user-1",
                tenant_key="default",
                org_id="org-1",
                signal_id="signal-1",
                dataset_id="dataset-1",
            )

        self.assertEqual(response.result_code, "warning")
        service._engine.execute.assert_awaited_once()
        dataset = service._engine.execute.await_args.kwargs["dataset"]
        self.assertIn("repositories", dataset)
        self.assertIn("workflows", dataset)
        self.assertEqual(len(dataset["repositories"]), 1)
        self.assertEqual(dataset["repositories"][0]["name"], "kreesalis/kcontrol")
        self.assertEqual(dataset["workflows"][0]["repository"], "kreesalis/kcontrol")
        self.assertEqual(len(dataset["records"]), 2)
        service._repository.insert_run.assert_awaited_once()

    async def test_batch_execute_raises_when_every_signal_execution_fails(self) -> None:
        connection = MagicMock()
        service = self._make_service(connection=connection)
        service.execute_signal = AsyncMock(side_effect=ValidationError("Dataset has no records to execute."))

        with self.assertRaises(ValidationError) as exc_info:
            await service.batch_execute(
                user_id="user-1",
                tenant_key="default",
                org_id="org-1",
                signal_ids=["signal-1", "signal-2"],
                dataset_id="dataset-1",
            )

        self.assertIn("No signals executed successfully", str(exc_info.exception))

    async def test_batch_execute_keeps_successful_runs_when_only_some_fail(self) -> None:
        connection = MagicMock()
        service = self._make_service(connection=connection)
        success = RunResponse(
            id="run-1",
            tenant_key="default",
            org_id="org-1",
            signal_id="signal-1",
            signal_code="github_actions_workflow_activity_and_integrity",
            dataset_id="dataset-1",
            live_session_id=None,
            execution_status_code="completed",
            execution_status_name=None,
            result_code="warning",
            result_summary="workflow issues detected",
            result_details=[],
            execution_time_ms=10,
            error_message=None,
            stdout_capture=None,
            started_at="2026-03-24T00:00:00+00:00",
            completed_at="2026-03-24T00:00:01+00:00",
            created_at="2026-03-24T00:00:01+00:00",
            signal_name="Signal 1",
        )
        service.execute_signal = AsyncMock(
            side_effect=[
                success,
                ValidationError("boom"),
            ]
        )

        response = await service.batch_execute(
            user_id="user-1",
            tenant_key="default",
            org_id="org-1",
            signal_ids=["signal-1", "signal-2"],
            dataset_id="dataset-1",
        )

        self.assertEqual(list(response.signal_results.keys()), ["signal-1"])

    async def test_batch_execute_normalizes_stringified_expression_nodes(self) -> None:
        connection = MagicMock()
        service = self._make_service(connection=connection)
        service.execute_signal = AsyncMock(
            return_value=RunResponse(
                id="run-1",
                tenant_key="default",
                org_id="org-1",
                signal_id="signal-1",
                signal_code="github_actions_workflow_integrity",
                dataset_id="dataset-1",
                live_session_id=None,
                execution_status_code="completed",
                execution_status_name=None,
                result_code="warning",
                result_summary="warning",
                result_details=[],
                execution_time_ms=10,
                error_message=None,
                stdout_capture=None,
                started_at="2026-03-24T00:00:00+00:00",
                completed_at="2026-03-24T00:00:01+00:00",
                created_at="2026-03-24T00:00:01+00:00",
                signal_name="Signal 1",
            )
        )
        threat_record = SimpleNamespace(
            id="threat-1",
            threat_code="github_actions_activity_integrity_gap_tt",
            expression_tree={
                "operator": "OR",
                "conditions": [
                    json.dumps(
                        {
                            "signal_code": "github_actions_workflow_integrity",
                            "expected_result": "warning",
                        }
                    )
                ],
            },
        )
        service._threat_repository.list_threat_types = AsyncMock(return_value=([threat_record], 1))
        service._policy_repository.list_policies = AsyncMock(
            return_value=(
                [
                    SimpleNamespace(
                        id="policy-1",
                        policy_code="github_actions_activity_integrity_gap_tt_policy",
                        actions=[json.dumps({"action_type": "notification", "config": {"channel": "in_app"}})],
                    )
                ],
                1,
            )
        )

        response = await service.batch_execute(
            user_id="user-1",
            tenant_key="default",
            org_id="org-1",
            signal_ids=["signal-1"],
            dataset_id="dataset-1",
        )

        self.assertEqual(len(response.threat_evaluations), 1)
        self.assertTrue(response.threat_evaluations[0].is_triggered)
        self.assertEqual(len(response.policy_executions), 1)


class ExecutionRepositoryParsingTests(unittest.TestCase):
    def test_parse_json_decodes_double_encoded_dict(self) -> None:
        encoded = json.dumps(json.dumps({"signal": "warning"}))
        self.assertEqual(parse_json(encoded), {"signal": "warning"})

    def test_parse_json_list_decodes_double_encoded_list(self) -> None:
        encoded = json.dumps(json.dumps([{"action_type": "notification"}]))
        self.assertEqual(parse_json_list(encoded), [{"action_type": "notification"}])
