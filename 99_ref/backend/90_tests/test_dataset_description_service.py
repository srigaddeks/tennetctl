from __future__ import annotations

import unittest
from importlib import import_module as stdlib_import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = stdlib_import_module("backend.10_sandbox.03_datasets.service")

DatasetService = service_module.DatasetService


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


class _FakeRepository:
    def __init__(self, *, batches: list[tuple[int, list[SimpleNamespace], int]]) -> None:
        self._batches = {offset: (records, total) for offset, records, total in batches}
        self.list_calls: list[tuple[int, int]] = []

    async def get_dataset_by_id(self, _conn, dataset_id: str):
        return SimpleNamespace(id=dataset_id)

    async def list_records(self, _conn, _dataset_id: str, *, limit: int, offset: int):
        self.list_calls.append((limit, offset))
        records, total = self._batches.get(offset, ([], 0))
        return records, total


class _FakeDatasetAgentService:
    def __init__(self, *, database_pool, settings) -> None:
        self._database_pool = database_pool
        self._settings = settings

    async def explain_record(self, **_kwargs) -> dict:
        return {
            "record_summary": "Synthetic summary",
            "fields": [],
            "recommended_signals": [],
        }


class DatasetDescriptionServiceTests(unittest.IsolatedAsyncioTestCase):
    def _make_service(self, *, connection, repository: _FakeRepository) -> DatasetService:
        service = DatasetService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(),
        )
        service._repository = repository
        service._logger = MagicMock()
        return service

    async def test_generate_descriptions_processes_all_dataset_pages(self) -> None:
        connection = MagicMock()
        connection.execute = AsyncMock()
        first_page = [
            SimpleNamespace(id=f"record-{idx}", record_data={"index": idx})
            for idx in range(50)
        ]
        second_page = [
            SimpleNamespace(id=f"record-{idx}", record_data={"index": idx})
            for idx in range(50, 60)
        ]
        repository = _FakeRepository(
            batches=[
                (0, first_page, 60),
                (50, second_page, 60),
            ]
        )
        service = self._make_service(connection=connection, repository=repository)

        def _fake_import_module(name: str):
            if name == "backend.20_ai.27_dataset_agent.service":
                return SimpleNamespace(DatasetAgentService=_FakeDatasetAgentService)
            return stdlib_import_module(name)

        with patch.object(service_module, "require_permission", AsyncMock()):
            with patch.object(service_module, "import_module", side_effect=_fake_import_module):
                result = await service.generate_descriptions(
                    user_id="user-1",
                    org_id="org-1",
                    dataset_id="dataset-1",
                    asset_type="github_workflow",
                    connector_type="github",
                )

        self.assertEqual(result, {"updated": 60, "total": 60})
        self.assertEqual(repository.list_calls, [(50, 0), (50, 50)])
        self.assertEqual(connection.execute.await_count, 60)
