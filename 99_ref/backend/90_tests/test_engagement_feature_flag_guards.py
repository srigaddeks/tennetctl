from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


router_module = import_module("backend.12_engagements.router")

ServiceUnavailableError = import_module("backend.01_core.errors").ServiceUnavailableError


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


def _make_request() -> SimpleNamespace:
    connection = MagicMock()
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                database_pool=_FakePool(connection),
            )
        )
    )


def _make_claims() -> SimpleNamespace:
    return SimpleNamespace(
        subject="user-1",
        tenant_key="tenant-1",
        portal_mode=None,
        is_api_key=False,
    )


class EngagementFeatureFlagGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_my_engagements_blocks_when_portfolio_flag_disabled(self) -> None:
        flag_guard = AsyncMock(side_effect=ServiceUnavailableError("disabled"))

        with patch.object(router_module, "_get_service", return_value=MagicMock()), patch.object(
            router_module, "require_feature_flag_enabled", flag_guard
        ):
            with self.assertRaises(ServiceUnavailableError):
                await router_module.list_my_engagements(
                    request=_make_request(),
                    claims=_make_claims(),
                )

        self.assertEqual(flag_guard.await_args.kwargs["flag_code"], "audit_workspace_auditor_portfolio")

    async def test_controls_blocks_when_control_access_flag_disabled(self) -> None:
        flag_guard = AsyncMock(side_effect=ServiceUnavailableError("disabled"))

        with patch.object(router_module, "_get_service", return_value=MagicMock()), patch.object(
            router_module, "require_feature_flag_enabled", flag_guard
        ):
            with self.assertRaises(ServiceUnavailableError):
                await router_module.list_engagement_controls(
                    request=_make_request(),
                    engagement_id="eng-1",
                    claims=_make_claims(),
                )

        self.assertEqual(flag_guard.await_args.kwargs["flag_code"], "audit_workspace_control_access")

    async def test_requests_blocks_when_evidence_flag_disabled(self) -> None:
        flag_guard = AsyncMock(side_effect=ServiceUnavailableError("disabled"))

        with patch.object(router_module, "_get_service", return_value=MagicMock()), patch.object(
            router_module, "require_feature_flag_enabled", flag_guard
        ):
            with self.assertRaises(ServiceUnavailableError):
                await router_module.list_auditor_requests(
                    request=_make_request(),
                    engagement_id="eng-1",
                    claims=_make_claims(),
                )

        self.assertEqual(flag_guard.await_args.kwargs["flag_code"], "audit_workspace_evidence_requests")

    async def test_tasks_blocks_when_task_flag_disabled(self) -> None:
        flag_guard = AsyncMock(side_effect=ServiceUnavailableError("disabled"))

        with patch.object(router_module, "_get_service", return_value=MagicMock()), patch.object(
            router_module, "require_feature_flag_enabled", flag_guard
        ):
            with self.assertRaises(ServiceUnavailableError):
                await router_module.list_engagement_tasks(
                    request=_make_request(),
                    engagement_id="eng-1",
                    task_service=MagicMock(),
                    claims=_make_claims(),
                )

        self.assertEqual(flag_guard.await_args.kwargs["flag_code"], "audit_workspace_auditor_tasks")

    async def test_findings_blocks_when_findings_flag_disabled(self) -> None:
        flag_guard = AsyncMock(side_effect=ServiceUnavailableError("disabled"))

        with patch.object(router_module, "_get_service", return_value=MagicMock()), patch.object(
            router_module, "require_feature_flag_enabled", flag_guard
        ):
            with self.assertRaises(ServiceUnavailableError):
                await router_module.list_engagement_assessments(
                    request=_make_request(),
                    engagement_id="eng-1",
                    claims=_make_claims(),
                )

        self.assertEqual(flag_guard.await_args.kwargs["flag_code"], "audit_workspace_auditor_findings")


if __name__ == "__main__":
    unittest.main()
