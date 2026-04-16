from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import asyncpg


service_module = import_module("backend.12_engagements.service")


class _TransactionContext:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeConnection:
    def transaction(self):
        return _TransactionContext()


class EngagementRequestConcurrencyGuardTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.repo = SimpleNamespace(
            list_access_tokens=AsyncMock(
                return_value=[
                    SimpleNamespace(id="token-1", auditor_email="auditor@example.com"),
                ]
            ),
            get_open_auditor_request_id=AsyncMock(return_value=None),
            get_latest_dismissed_auditor_request_description=AsyncMock(return_value=None),
            get_latest_dismissed_auditor_request_at=AsyncMock(return_value=None),
            create_auditor_request=AsyncMock(return_value="req-1"),
            fulfill_auditor_request=AsyncMock(return_value=False),
        )
        self.service = service_module.EngagementService(self.repo)
        self.service._audit_writer = MagicMock(write_entry=AsyncMock())
        self.connection = _FakeConnection()

    async def test_create_auditor_request_converts_unique_violation_into_friendly_error(self) -> None:
        self.repo.create_auditor_request.side_effect = asyncpg.UniqueViolationError()

        with self.assertRaises(ValueError) as exc_info:
            await self.service.create_auditor_request(
                None,
                engagement_id="eng-1",
                tenant_key="tenant-1",
                control_id="ctrl-1",
                email="auditor@example.com",
                description="Need payroll sample for Q4 variance investigation",
            )

        self.assertIn("already exists", str(exc_info.exception))
        self.service._audit_writer.write_entry.assert_not_awaited()

    async def test_fulfill_auditor_request_skips_audit_when_second_reviewer_loses_race(self) -> None:
        success = await self.service.fulfill_auditor_request(
            self.connection,
            "req-1",
            "tenant-1",
            action="fulfill",
            fulfilled_by="00000000-0000-0000-0000-000000000010",
            attachment_id="00000000-0000-0000-0000-000000000011",
        )

        self.assertFalse(success)
        self.repo.fulfill_auditor_request.assert_awaited_once()
        self.service._audit_writer.write_entry.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
