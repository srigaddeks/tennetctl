from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.10_sandbox.10_promotions.service")

PromotionService = service_module.PromotionService
PromotePolicyRequest = service_module.PromotePolicyRequest


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


class PromotionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_promote_policy_inserts_promotion_before_promoted_test(self) -> None:
        connection = MagicMock()
        service = PromotionService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(delete=AsyncMock()),
        )
        service._audit_writer = SimpleNamespace(write_entry=AsyncMock())

        call_order: list[str] = []

        async def _record(label: str, result=None):
            call_order.append(label)
            return result

        async def _insert_promotion(*_args, **_kwargs):
            return await _record("insert_promotion")

        async def _deactivate_versions(*_args, **_kwargs):
            return await _record("deactivate_versions")

        async def _create_promoted_test(*_args, **_kwargs):
            return await _record("create_promoted_test")

        service._repository = SimpleNamespace(
            get_policy_for_promotion=AsyncMock(
                return_value={
                    "id": "policy-1",
                    "tenant_key": "default",
                    "org_id": "org-1",
                    "policy_code": "github_policy_gap",
                    "threat_type_id": "threat-1",
                    "threat_code": "github_policy_gap_tt",
                    "name": "GitHub Policy Gap",
                    "description": "policy description",
                    "policy_container_code": "github",
                    "policy_container_name": "GitHub",
                }
            ),
            create_control_test=AsyncMock(return_value="test-1"),
            upsert_control_test_properties=AsyncMock(),
            insert_promotion=AsyncMock(side_effect=_insert_promotion),
            get_next_promoted_version=AsyncMock(return_value=1),
            deactivate_promoted_versions=AsyncMock(side_effect=_deactivate_versions),
            create_promoted_test=AsyncMock(side_effect=_create_promoted_test),
            upsert_promoted_test_properties=AsyncMock(),
        )
        service._get_promotion = AsyncMock(
            return_value=SimpleNamespace(
                id="promotion-1",
                tenant_key="default",
                signal_id=None,
                policy_id="policy-1",
                library_id=None,
                target_test_id="test-1",
                target_test_code="sb_github_policy_gap",
                source_name="GitHub Policy Gap",
                source_code="github_policy_gap",
                promotion_status="promoted",
                promoted_at="2026-03-24T00:00:00+00:00",
                promoted_by="user-1",
                review_notes=None,
                created_at="2026-03-24T00:00:00+00:00",
                created_by="user-1",
            )
        )

        connection.fetchrow = AsyncMock(return_value={"id": "eval-1"})

        with (
            patch.object(service_module, "require_permission", AsyncMock()),
            patch.object(service_module, "write_lifecycle_event", AsyncMock()),
        ):
            response = await service.promote_policy(
                user_id="user-1",
                tenant_key="default",
                policy_id="policy-1",
                request=PromotePolicyRequest(),
            )

        self.assertEqual(response.policy_id, "policy-1")
        self.assertIn("insert_promotion", call_order)
        self.assertIn("create_promoted_test", call_order)
        self.assertLess(call_order.index("insert_promotion"), call_order.index("create_promoted_test"))
        control_test_kwargs = service._repository.create_control_test.await_args.kwargs
        self.assertEqual(control_test_kwargs["integration_type"], "github")
        promoted_props = service._repository.upsert_promoted_test_properties.await_args.args[2]
        self.assertEqual(promoted_props["policy_container_code"], "github")
        self.assertEqual(promoted_props["policy_container_name"], "GitHub")
