from __future__ import annotations

import unittest
from importlib import import_module
from uuid import uuid4


repository_module = import_module("backend.12_engagements.repository")


class _FakeConnection:
    def __init__(self) -> None:
        self.fetchrow_sql: str | None = None
        self.fetchrow_args = None

    async def fetchrow(self, sql: str, *args):
        self.fetchrow_sql = sql
        self.fetchrow_args = args
        return {
            "id": str(uuid4()),
            "engagement_id": str(uuid4()),
            "control_id": str(uuid4()),
            "request_status": "open",
            "auditor_email": "auditor@example.com",
            "membership_id": str(uuid4()),
        }


class EngagementRequestLockingTests(unittest.IsolatedAsyncioTestCase):
    async def test_lock_request_for_review_uses_row_lock(self) -> None:
        connection = _FakeConnection()
        repo = repository_module.EngagementRepository()

        row = await repo._lock_request_for_review(
            connection,
            request_id=str(uuid4()),
            tenant_key="tenant-1",
        )

        self.assertIsNotNone(row)
        self.assertIsNotNone(connection.fetchrow_sql)
        assert connection.fetchrow_sql is not None
        self.assertIn("FOR UPDATE", connection.fetchrow_sql.upper())


if __name__ == "__main__":
    unittest.main()
