from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


service_module = import_module("backend.12_engagements.service")


class EngagementRequestResubmissionRuleTests(unittest.IsolatedAsyncioTestCase):
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
        )
        self.service = service_module.EngagementService(self.repo)
        self.service._audit_writer = MagicMock(write_entry=AsyncMock())

    async def test_rejected_request_requires_fresh_justification(self) -> None:
        self.repo.get_latest_dismissed_auditor_request_description.return_value = "Need payroll sample"

        with self.assertRaises(ValueError) as exc_info:
            await self.service.create_auditor_request(
                None,
                engagement_id="eng-1",
                tenant_key="tenant-1",
                control_id="ctrl-1",
                email="auditor@example.com",
                description="  Need   payroll   sample  ",
            )

        self.assertIn("fresh justification", str(exc_info.exception))
        self.repo.create_auditor_request.assert_not_awaited()

    async def test_rejected_request_cooldown_blocks_immediate_resubmission(self) -> None:
        self.repo.get_latest_dismissed_auditor_request_description.return_value = "Need payroll sample"
        self.repo.get_latest_dismissed_auditor_request_at.return_value = datetime.now() - timedelta(minutes=5)

        with self.assertRaises(ValueError) as exc_info:
            await self.service.create_auditor_request(
                None,
                engagement_id="eng-1",
                tenant_key="tenant-1",
                control_id="ctrl-1",
                email="auditor@example.com",
                description="Need payroll sample for Q4 variance investigation",
            )

        self.assertIn("Please wait", str(exc_info.exception))
        self.repo.create_auditor_request.assert_not_awaited()

    async def test_rejected_request_can_be_resubmitted_with_new_justification(self) -> None:
        self.repo.get_latest_dismissed_auditor_request_description.return_value = "Need payroll sample"
        self.repo.get_latest_dismissed_auditor_request_at.return_value = datetime.now() - timedelta(minutes=20)

        request_id = await self.service.create_auditor_request(
            None,
            engagement_id="eng-1",
            tenant_key="tenant-1",
            control_id="ctrl-1",
            email="auditor@example.com",
            description="Need payroll sample for Q4 variance investigation",
        )

        self.assertEqual(request_id, "req-1")
        self.repo.create_auditor_request.assert_awaited_once()
        kwargs = self.repo.create_auditor_request.await_args.kwargs
        self.assertEqual(kwargs["description"], "Need payroll sample for Q4 variance investigation")

    async def test_blank_request_description_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as exc_info:
            await self.service.create_auditor_request(
                None,
                engagement_id="eng-1",
                tenant_key="tenant-1",
                control_id="ctrl-1",
                email="auditor@example.com",
                description="   ",
            )

        self.assertIn("description is required", str(exc_info.exception))
        self.repo.list_access_tokens.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
