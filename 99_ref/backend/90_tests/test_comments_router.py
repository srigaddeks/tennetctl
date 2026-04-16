from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace


router_module = import_module("backend.08_comments.01_comments.router")

NotFoundError = router_module.NotFoundError


class _FakeConnection:
    def __init__(self, *, row=None) -> None:
        self._row = row
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetchrow(self, query: str, *args):
        self.calls.append((query, args))
        return self._row


class _FakeCommentRepository:
    async def get_comment_by_id(self, conn, comment_id: str):
        if comment_id != "comment-123":
            return None
        return SimpleNamespace(entity_type="risk", entity_id="risk-123")


class _FakeCommentService:
    def __init__(self) -> None:
        self._repository = _FakeCommentRepository()


class CommentRouterScopeTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_entity_scope_uses_risk_record_scope(self) -> None:
        connection = _FakeConnection(row={"org_id": "org-db", "workspace_id": "ws-db"})

        org_id, workspace_id = await router_module._resolve_entity_scope(
            connection,
            tenant_key="default",
            entity_type="risk",
            entity_id="risk-123",
        )

        self.assertEqual((org_id, workspace_id), ("org-db", "ws-db"))
        self.assertEqual(len(connection.calls), 1)
        self.assertIn('"14_risk_registry"."10_fct_risks"', connection.calls[0][0])
        self.assertEqual(connection.calls[0][1], ("risk-123", "default"))

    async def test_require_comment_permission_uses_entity_scope_from_comment_record(self) -> None:
        service = _FakeCommentService()
        connection = _FakeConnection()
        captured: dict[str, tuple[object, ...]] = {}

        async def _fake_resolve(conn, *, tenant_key: str, entity_type: str, entity_id: str):
            captured["resolve"] = (tenant_key, entity_type, entity_id)
            return "org-from-db", "ws-from-db"

        async def _fake_require(
            conn,
            user_id: str,
            permission_code: str,
            *,
            scope_org_id: str | None = None,
            scope_workspace_id: str | None = None,
        ) -> None:
            captured["permission"] = (
                user_id,
                permission_code,
                scope_org_id,
                scope_workspace_id,
            )

        original_resolve = router_module._resolve_entity_scope
        original_require = router_module.require_permission
        router_module._resolve_entity_scope = _fake_resolve
        router_module.require_permission = _fake_require
        try:
            entity_type, entity_id, org_id, workspace_id = await router_module._require_comment_permission(
                connection,
                service=service,
                tenant_key="default",
                user_id="user-123",
                permission_code="comments.view",
                comment_id="comment-123",
            )
        finally:
            router_module._resolve_entity_scope = original_resolve
            router_module.require_permission = original_require

        self.assertEqual((entity_type, entity_id), ("risk", "risk-123"))
        self.assertEqual((org_id, workspace_id), ("org-from-db", "ws-from-db"))
        self.assertEqual(captured["resolve"], ("default", "risk", "risk-123"))
        self.assertEqual(
            captured["permission"],
            ("user-123", "comments.view", "org-from-db", "ws-from-db"),
        )

    async def test_resolve_entity_scope_rejects_removed_evidence_templates(self) -> None:
        connection = _FakeConnection()

        with self.assertRaises(NotFoundError):
            await router_module._resolve_entity_scope(
                connection,
                tenant_key="default",
                entity_type="evidence_template",
                entity_id="template-123",
            )
