from __future__ import annotations

import unittest
from importlib import import_module


repository_module = import_module("backend.07_tasks.02_tasks.repository")
TaskRepository = repository_module.TaskRepository


class _FakeConnection:
    def __init__(self) -> None:
        self.fetch_sql: list[str] = []
        self.fetchrow_sql: list[str] = []

    async def fetch(self, sql: str, *args):
        self.fetch_sql.append(sql)
        if "GROUP BY v.status_code" in sql:
            return [{"status_code": "open", "cnt": 2}]
        if "GROUP BY v.task_type_code" in sql:
            return [{"task_type_code": "remediation", "task_type_name": "Remediation", "cnt": 2}]
        return []

    async def fetchrow(self, sql: str, *args):
        self.fetchrow_sql.append(sql)
        return {"cnt": 0}


class TaskRepositorySummaryQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_task_summary_uses_detail_view_for_engagement_filtering(self) -> None:
        connection = _FakeConnection()
        repository = TaskRepository()

        result = await repository.get_task_summary(
            connection,
            tenant_key="tenant-1",
            org_id="00000000-0000-0000-0000-000000000001",
            workspace_id="00000000-0000-0000-0000-000000000002",
            accessible_engagement_ids=["00000000-0000-0000-0000-000000000003"],
        )

        self.assertEqual(result["open_count"], 2)
        all_sql = "\n".join(connection.fetch_sql + connection.fetchrow_sql)
        self.assertIn('"40_vw_task_detail" AS v', all_sql)
        self.assertNotIn('"10_fct_tasks" AS t WHERE', all_sql)
        self.assertIn("v.entity_type = 'engagement'", all_sql)
        self.assertIn("ANY($4::uuid[])", all_sql)


if __name__ == "__main__":
    unittest.main()
