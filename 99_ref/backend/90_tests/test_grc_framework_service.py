from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace


service_module = import_module("backend.05_grc_library.02_frameworks.service")

FrameworkService = service_module.FrameworkService
AuditEntry = service_module.AuditEntry


class _AsyncContextManager:
    def __init__(self, value) -> None:
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeDatabasePool:
    def __init__(self, connection) -> None:
        self._connection = connection

    def transaction(self) -> _AsyncContextManager:
        return _AsyncContextManager(self._connection)


class _FakeCache:
    def __init__(self) -> None:
        self.deleted_patterns: list[str] = []

    async def delete_pattern(self, pattern: str) -> None:
        self.deleted_patterns.append(pattern)


class _FakeAuditWriter:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def write_entry(self, conn, entry: AuditEntry) -> None:
        self.entries.append(entry)


class _FakeFrameworkRepository:
    def __init__(self, framework) -> None:
        self._framework = framework
        self.deleted_framework_ids: list[str] = []

    async def get_framework_by_id(self, conn, framework_id: str):
        return self._framework if framework_id == self._framework.id else None

    async def soft_delete_framework_graph(
        self,
        conn,
        framework_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        self.deleted_framework_ids.append(framework_id)
        return framework_id == self._framework.id

    async def has_published_versions(self, conn, framework_id: str) -> bool:
        raise AssertionError("delete_framework should not call has_published_versions")


class FrameworkServiceDeleteTests(unittest.IsolatedAsyncioTestCase):
    async def test_delete_framework_uses_graph_soft_delete_and_invalidates_cache(self) -> None:
        framework = SimpleNamespace(
            id="framework-123",
            scope_org_id=None,
            scope_workspace_id=None,
            tenant_key="default",
            framework_code="delete-fw",
        )
        connection = object()
        repository = _FakeFrameworkRepository(framework)
        cache = _FakeCache()
        audit_writer = _FakeAuditWriter()

        service = FrameworkService(
            settings=SimpleNamespace(),
            database_pool=_FakeDatabasePool(connection),
            cache=cache,
        )
        service._repository = repository
        service._audit_writer = audit_writer

        permission_calls: list[tuple[str, str | None, str | None]] = []

        async def _record_permission(
            conn,
            *,
            user_id: str,
            permission_code: str,
            scope_org_id: str | None,
            scope_workspace_id: str | None,
        ) -> None:
            permission_calls.append((permission_code, scope_org_id, scope_workspace_id))

        service._require_framework_permission = _record_permission

        await service.delete_framework(user_id="user-123", framework_id=framework.id)

        self.assertEqual(repository.deleted_framework_ids, [framework.id])
        self.assertEqual(permission_calls, [("frameworks.delete", None, None)])
        self.assertEqual(cache.deleted_patterns, ["frameworks:list:*"])
        self.assertEqual(len(audit_writer.entries), 1)
        self.assertEqual(audit_writer.entries[0].entity_id, framework.id)
        self.assertEqual(audit_writer.entries[0].event_type, "framework_deleted")
