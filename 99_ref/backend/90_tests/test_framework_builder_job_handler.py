from __future__ import annotations

from importlib import import_module
import unittest
from unittest.mock import AsyncMock, call


job_handler_module = import_module("backend.20_ai.21_framework_builder.job_handler")


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


class FrameworkBuilderRiskSyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_sync_reuses_workspace_deployment_risk_id(self) -> None:
        connection = AsyncMock()
        connection.fetch = AsyncMock(
            return_value=[
                {
                    "global_risk_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "risk_code": "ACC-001",
                    "risk_category_code": "technology",
                    "risk_level_code": "high",
                    "title": "Unauthorized access",
                    "description": "Access control failure.",
                    "control_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "mapping_type": "mitigating",
                }
            ]
        )
        connection.fetchrow = AsyncMock(
            return_value={"workspace_risk_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"}
        )
        connection.execute = AsyncMock()
        pool = _FakePool(connection)

        result = await job_handler_module._sync_workspace_risk_registry_links(
            pool=pool,
            tenant_key="tenant-1",
            user_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
            framework_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            scope_org_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
            scope_workspace_id="11111111-2222-3333-4444-555555555555",
        )

        self.assertEqual(result, {"risk_count": 1, "link_count": 1})
        link_calls = [args for args in connection.execute.await_args_list if '"14_risk_registry"."30_lnk_risk_control_mappings"' in args.args[0]]
        self.assertEqual(len(link_calls), 1)
        self.assertEqual(link_calls[0].args[1], "cccccccc-cccc-cccc-cccc-cccccccccccc")

    async def test_sync_fallback_creates_workspace_suffixed_risk_and_deployment(self) -> None:
        connection = AsyncMock()
        connection.fetch = AsyncMock(
            return_value=[
                {
                    "global_risk_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "risk_code": "ACC-001",
                    "risk_category_code": "technology",
                    "risk_level_code": "high",
                    "title": "Unauthorized access",
                    "description": "Access control failure.",
                    "control_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "mapping_type": "mitigating",
                }
            ]
        )
        connection.fetchrow = AsyncMock(side_effect=[None, None])
        connection.execute = AsyncMock()
        pool = _FakePool(connection)

        result = await job_handler_module._sync_workspace_risk_registry_links(
            pool=pool,
            tenant_key="tenant-1",
            user_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
            framework_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            scope_org_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
            scope_workspace_id="11111111-2222-3333-4444-555555555555",
        )

        self.assertEqual(result, {"risk_count": 1, "link_count": 1})
        execute_sql = [args.args[0] for args in connection.execute.await_args_list]
        self.assertTrue(
            any('"14_risk_registry"."10_fct_risks"' in sql for sql in execute_sql),
        )
        risk_insert_calls = [args for args in connection.execute.await_args_list if '"14_risk_registry"."10_fct_risks"' in args.args[0]]
        self.assertEqual(len(risk_insert_calls), 1)
        inserted_risk_code = risk_insert_calls[0].args[3]
        self.assertEqual(inserted_risk_code, "ACC-001__ws_11111111")
        self.assertTrue(
            any('"05_grc_library"."17_fct_risk_library_deployments"' in sql for sql in execute_sql),
        )
