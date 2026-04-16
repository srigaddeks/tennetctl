from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


router_module = import_module("backend.12_engagements.router")


class EngagementRouterAccessGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_engagement_access_v2_blocks_suspended_user(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
        )

        with self.assertRaises(HTTPException) as exc_info:
            await router_module._resolve_engagement_access_v2(
                None,
                service,
                "eng-1",
                claims,
            )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("inactive or suspended", str(exc_info.exception.detail))
        service.is_user_globally_active.assert_awaited_once()

    async def test_resolve_engagement_access_v2_denies_non_member_without_guest_or_grc_access(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_engagement=AsyncMock(return_value=None),
            get_active_membership_access=AsyncMock(return_value=None),
            validate_auditor_access_and_get_tenant=AsyncMock(return_value=None),
        )

        with patch.object(router_module, "_get_auditor_email", AsyncMock(return_value="user@example.com")):
            with self.assertRaises(HTTPException) as exc_info:
                await router_module._resolve_engagement_access_v2(
                    None,
                    service,
                    "eng-1",
                    claims,
                )

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertIn("access denied", str(exc_info.exception.detail))
        service.get_active_membership_access.assert_awaited_once()
        service.validate_auditor_access_and_get_tenant.assert_awaited_once()

    async def test_list_engagement_tasks_denies_non_owner_without_active_membership(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        engagement = SimpleNamespace(org_id="org-1", workspace_id="ws-1")
        service = SimpleNamespace(
            get_engagement=AsyncMock(return_value=engagement),
            get_active_membership_access=AsyncMock(return_value=None),
        )

        with patch.object(router_module, "_get_service", return_value=service), patch.object(
            router_module, "require_feature_flag_enabled", AsyncMock()
        ), patch.object(
            router_module, "_resolve_engagement_access_v2", AsyncMock(return_value=("tenant-1", False))
        ):
            with self.assertRaises(HTTPException) as exc_info:
                await router_module.list_engagement_tasks(
                    request=request,
                    engagement_id="eng-1",
                    task_service=MagicMock(),
                    claims=claims,
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Active engagement membership is required", str(exc_info.exception.detail))
        service.get_active_membership_access.assert_awaited_once()

    async def test_list_engagement_controls_passes_membership_scope_for_auditor(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        service = SimpleNamespace(
            get_active_membership_access=AsyncMock(
                return_value={"membership_id": "mem-1"},
            ),
            list_engagement_controls=AsyncMock(return_value=[{"id": "ctrl-1"}]),
        )

        with patch.object(router_module, "_get_service", return_value=service), patch.object(
            router_module, "require_feature_flag_enabled", AsyncMock()
        ), patch.object(
            router_module, "_resolve_engagement_access_v2", AsyncMock(return_value=("tenant-1", False))
        ):
            result = await router_module.list_engagement_controls(
                request=request,
                engagement_id="eng-1",
                claims=claims,
            )

        self.assertEqual(result, [{"id": "ctrl-1"}])
        service.list_engagement_controls.assert_awaited_once()
        kwargs = service.list_engagement_controls.await_args.kwargs
        self.assertTrue(kwargs["auditor_only"])
        self.assertEqual(kwargs["viewer_membership_id"], "mem-1")

    async def test_list_engagement_controls_denies_non_owner_without_active_membership(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        service = SimpleNamespace(
            get_active_membership_access=AsyncMock(return_value=None),
            list_engagement_controls=AsyncMock(),
        )

        with patch.object(router_module, "_get_service", return_value=service), patch.object(
            router_module, "require_feature_flag_enabled", AsyncMock()
        ), patch.object(
            router_module, "_resolve_engagement_access_v2", AsyncMock(return_value=("tenant-1", False))
        ):
            with self.assertRaises(HTTPException) as exc_info:
                await router_module.list_engagement_controls(
                    request=request,
                    engagement_id="eng-1",
                    claims=claims,
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Active engagement membership is required for auditor control access", str(exc_info.exception.detail))
        service.list_engagement_controls.assert_not_awaited()

    async def test_request_more_docs_allows_membership_based_auditor(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_active_membership_access=AsyncMock(return_value={"membership_id": "mem-1"}),
            create_auditor_request=AsyncMock(return_value="req-1"),
        )

        with patch.object(router_module, "_get_service", return_value=service), patch.object(
            router_module, "require_feature_flag_enabled", AsyncMock()
        ), patch.object(
            router_module, "_resolve_engagement_access_v2", AsyncMock(return_value=("tenant-1", False))
        ), patch.object(
            router_module, "_get_auditor_email", AsyncMock(return_value="auditor@example.com")
        ):
            result = await router_module.request_more_docs(
                request=request,
                engagement_id="eng-1",
                control_id="ctrl-1",
                data=SimpleNamespace(description="Need walkthrough evidence."),
                claims=claims,
            )

        self.assertEqual(result, {"id": "req-1"})
        service.create_auditor_request.assert_awaited_once()
        kwargs = service.create_auditor_request.await_args.kwargs
        self.assertEqual(kwargs["tenant_key"], "tenant-1")
        self.assertEqual(kwargs["email"], "auditor@example.com")

    async def test_list_engagement_assessments_denies_non_owner_without_active_membership(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        service = SimpleNamespace(
            get_engagement=AsyncMock(return_value=SimpleNamespace(id="eng-1")),
            get_active_membership_access=AsyncMock(return_value=None),
            list_assessments_in_engagement_scope=AsyncMock(),
        )

        with patch.object(router_module, "_get_service", return_value=service), patch.object(
            router_module, "require_feature_flag_enabled", AsyncMock()
        ), patch.object(
            router_module, "_resolve_engagement_access_v2", AsyncMock(return_value=("tenant-1", False))
        ):
            with self.assertRaises(HTTPException) as exc_info:
                await router_module.list_engagement_assessments(
                    request=request,
                    engagement_id="eng-1",
                    claims=claims,
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Active engagement membership is required for auditor assessment access", str(exc_info.exception.detail))
        service.list_assessments_in_engagement_scope.assert_not_awaited()

    async def test_list_access_tokens_blocks_suspended_user(self) -> None:
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database_pool=SimpleNamespace(
                        acquire=lambda: _AcquireContext(MagicMock()),
                    )
                )
            )
        )
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", portal_mode=None, is_api_key=False)
        service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
        )

        with patch.object(router_module, "_get_service", return_value=service):
            with self.assertRaises(HTTPException) as exc_info:
                await router_module.list_access_tokens(
                    request=request,
                    engagement_id="eng-1",
                    claims=claims,
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("inactive or suspended", str(exc_info.exception.detail))
        service.is_user_globally_active.assert_awaited_once()

class _AcquireContext:
    def __init__(self, connection) -> None:
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


if __name__ == "__main__":
    unittest.main()
