from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


service_module = import_module("backend.10_sandbox.06_policies.service")

PolicyService = service_module.PolicyService
ValidationError = service_module.ValidationError


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


class _FakeRepository:
    def __init__(self) -> None:
        self.created_payloads: list[dict] = []
        self.upserted_properties: list[dict[str, str]] = []

    async def get_next_version(self, _conn, _org_id: str, _policy_code: str) -> int:
        return 1

    async def create_policy(self, _conn, **kwargs) -> None:
        self.created_payloads.append(kwargs)

    async def upsert_properties(self, _conn, _policy_id: str, _properties: dict[str, str], **_kwargs) -> None:
        self.upserted_properties.append(_properties)
        return None

    async def get_policy_by_id(self, _conn, policy_id: str):
        return SimpleNamespace(
            id=policy_id,
            tenant_key="default",
            org_id="org-1",
            workspace_id=None,
            policy_code="github_alert_policy",
            version_number=1,
            threat_type_id="threat-1",
            threat_code="github_workflow_review_required",
            actions=[{"action_type": "notification", "config": {"channel": "email"}}],
            is_enabled=False,
            cooldown_minutes=60,
            is_active=True,
            created_at="2026-03-24T00:00:00+00:00",
            updated_at="2026-03-24T00:00:00+00:00",
            name="GitHub alert policy",
            description="Test policy",
        )

    async def get_policy_properties(self, _conn, _policy_id: str) -> dict[str, str]:
        return {}


class PolicyServiceTests(unittest.IsolatedAsyncioTestCase):
    def _make_service(self, *, connection) -> PolicyService:
        service = PolicyService(
            settings=MagicMock(),
            database_pool=_FakePool(connection),
            cache=SimpleNamespace(delete=AsyncMock()),
        )
        service._repository = _FakeRepository()
        service._logger = MagicMock()
        return service

    async def test_create_policy_validates_against_sandbox_threat_types(self) -> None:
        connection = MagicMock()
        connection.fetchrow = AsyncMock(
            side_effect=[
                {"id": "threat-1"},
                {"code": "notification"},
            ]
        )
        service = self._make_service(connection=connection)

        request = service_module.CreatePolicyRequest(
            policy_code="github_alert_policy",
            threat_type_id="threat-1",
            actions=[{"action_type": "notification", "config": {"channel": "email"}}],
            is_enabled=False,
            cooldown_minutes=60,
            properties={
                "name": "GitHub alert policy",
                "policy_container_code": "github",
                "policy_container_name": "GitHub",
            },
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with patch.object(service._audit_writer, "write_entry", AsyncMock()):
                with patch.object(service_module, "write_lifecycle_event", AsyncMock()):
                    response = await service.create_policy(
                        user_id="user-1",
                        tenant_key="default",
                        org_id="org-1",
                        request=request,
                    )

        first_query = connection.fetchrow.await_args_list[0].args[0]
        self.assertIn('"23_fct_threat_types"', first_query)
        self.assertEqual(response.policy_code, "github_alert_policy")
        self.assertEqual(
            service._repository.upserted_properties[0]["policy_container_code"],
            "github",
        )
        self.assertEqual(
            service._repository.upserted_properties[0]["policy_container_name"],
            "GitHub",
        )

    async def test_create_policy_requires_container_selection(self) -> None:
        connection = MagicMock()
        connection.fetchrow = AsyncMock(
            side_effect=[
                {"id": "threat-1"},
                {"code": "notification"},
            ]
        )
        service = self._make_service(connection=connection)

        request = service_module.CreatePolicyRequest(
            policy_code="github_alert_policy",
            threat_type_id="threat-1",
            actions=[{"action_type": "notification", "config": {"channel": "email"}}],
            is_enabled=False,
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with self.assertRaises(ValidationError) as exc_info:
                await service.create_policy(
                    user_id="user-1",
                    tenant_key="default",
                    org_id="org-1",
                    request=request,
                )

        self.assertIn("Policy container selection is required", str(exc_info.exception))

    async def test_create_policy_raises_when_threat_type_missing(self) -> None:
        connection = MagicMock()
        connection.fetchrow = AsyncMock(return_value=None)
        service = self._make_service(connection=connection)

        request = service_module.CreatePolicyRequest(
            policy_code="github_alert_policy",
            threat_type_id="missing-threat",
            actions=[{"action_type": "notification", "config": {"channel": "email"}}],
            is_enabled=False,
        )

        with patch.object(service_module, "require_permission", AsyncMock()):
            with self.assertRaises(ValidationError) as exc_info:
                await service.create_policy(
                    user_id="user-1",
                    tenant_key="default",
                    org_id="org-1",
                    request=request,
                )

        self.assertIn("missing-threat", str(exc_info.exception))
