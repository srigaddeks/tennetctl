from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


router_module = import_module("backend.09_attachments.01_attachments.router")

AuthorizationError = router_module.AuthorizationError


class AttachmentEngagementGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_engagement_attachment_scope_blocks_suspended_user(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        fake_service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
        )

        with patch.object(router_module, "_get_engagement_service", return_value=fake_service):
            with self.assertRaises(AuthorizationError):
                await router_module._resolve_engagement_attachment_scope(
                    MagicMock(),
                    "eng-1",
                    claims,
                )

        fake_service.is_user_globally_active.assert_awaited_once()

    async def test_assert_attachment_engagement_boundary_blocks_suspended_user(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        attachment_service = SimpleNamespace(
            _repository=SimpleNamespace(
                get_attachment_by_id=AsyncMock(
                    return_value=SimpleNamespace(auditor_access=False),
                ),
            ),
        )
        fake_engagement_service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=False),
        )

        with patch.object(router_module, "_get_engagement_service", return_value=fake_engagement_service):
            with self.assertRaises(AuthorizationError):
                await router_module._assert_attachment_engagement_boundary(
                    MagicMock(),
                    attachment_service,
                    "att-1",
                    claims,
                )

        attachment_service._repository.get_attachment_by_id.assert_awaited_once()
        fake_engagement_service.is_user_globally_active.assert_awaited_once()

    async def test_assert_attachment_engagement_boundary_blocks_member_without_grant_for_private_evidence(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        attachment_service = SimpleNamespace(
            _repository=SimpleNamespace(
                get_attachment_by_id=AsyncMock(
                    return_value=SimpleNamespace(auditor_access=False),
                ),
                list_attachment_engagement_contexts=AsyncMock(
                    return_value=[{"engagement_id": "eng-1"}],
                ),
                has_active_creator_approved_evidence_grant=AsyncMock(return_value=False),
            ),
        )
        fake_engagement_service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_engagement=AsyncMock(return_value=None),
            get_active_membership_access=AsyncMock(
                return_value={"membership_id": "mem-1"},
            ),
            validate_auditor_access_and_get_tenant=AsyncMock(return_value=None),
        )

        with patch.object(router_module, "_get_engagement_service", return_value=fake_engagement_service), patch.object(
            router_module, "_get_user_email", AsyncMock(return_value=None)
        ):
            with self.assertRaises(AuthorizationError):
                await router_module._assert_attachment_engagement_boundary(
                    MagicMock(),
                    attachment_service,
                    "att-1",
                    claims,
                )

        attachment_service._repository.has_active_creator_approved_evidence_grant.assert_awaited_once()

    async def test_assert_attachment_engagement_boundary_allows_member_with_active_grant(self) -> None:
        claims = SimpleNamespace(subject="user-1", tenant_key="tenant-1", is_api_key=False)
        attachment_service = SimpleNamespace(
            _repository=SimpleNamespace(
                get_attachment_by_id=AsyncMock(
                    return_value=SimpleNamespace(auditor_access=False),
                ),
                list_attachment_engagement_contexts=AsyncMock(
                    return_value=[{"engagement_id": "eng-1"}],
                ),
                has_active_creator_approved_evidence_grant=AsyncMock(return_value=True),
            ),
        )
        fake_engagement_service = SimpleNamespace(
            is_user_globally_active=AsyncMock(return_value=True),
            get_engagement=AsyncMock(return_value=None),
            get_active_membership_access=AsyncMock(
                return_value={"membership_id": "mem-1"},
            ),
            validate_auditor_access_and_get_tenant=AsyncMock(return_value=None),
        )

        with patch.object(router_module, "_get_engagement_service", return_value=fake_engagement_service), patch.object(
            router_module, "_get_user_email", AsyncMock(return_value=None)
        ):
            await router_module._assert_attachment_engagement_boundary(
                MagicMock(),
                attachment_service,
                "att-1",
                claims,
            )

        attachment_service._repository.has_active_creator_approved_evidence_grant.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
