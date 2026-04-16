from __future__ import annotations

import unittest
from importlib import import_module
from uuid import uuid4


repository_module = import_module("backend.12_engagements.repository")


class _FetchValConnection:
    def __init__(self) -> None:
        self.sql: str | None = None
        self.args = None

    async def fetchval(self, sql: str, *args):
        self.sql = sql
        self.args = args
        return 1


class _FetchConnection:
    def __init__(self) -> None:
        self.sql: str | None = None
        self.args = None

    async def fetchrow(self, sql: str, *args):
        self.sql = sql
        self.args = args
        return {"total": 0}

    async def fetch(self, sql: str, *args):
        self.sql = sql
        self.args = args
        return []


class EngagementEvidenceLinkageQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_active_engagement_participants_includes_creator_fallback(self) -> None:
        connection = _FetchConnection()
        repo = repository_module.EngagementRepository()

        await repo.list_active_engagement_participants(
            connection,
            engagement_id=str(uuid4()),
        )

        assert connection.sql is not None
        self.assertIn("creator_participant AS", connection.sql)
        self.assertIn('COALESCE(NULLIF(wm.grc_role_code, \'\'), \'owner\') AS membership_type_code', connection.sql)
        self.assertIn("NOT EXISTS", connection.sql)

    async def test_list_engagements_qualifies_view_columns_when_joining_orgs(self) -> None:
        connection = _FetchConnection()
        repo = repository_module.EngagementRepository()

        await repo.list_engagements(
            connection,
            tenant_key="tenant-1",
            org_id=str(uuid4()),
            status_code="active",
        )

        assert connection.sql is not None
        self.assertIn("WHERE v.tenant_key = $1 AND v.org_id = $2 AND v.status_code = $3", connection.sql)
        self.assertIn("ORDER BY v.created_at DESC", connection.sql)

    async def test_list_engagement_controls_uses_two_args_for_owner_queries(self) -> None:
        connection = _FetchConnection()
        repo = repository_module.EngagementRepository()

        await repo.list_engagement_controls(
            connection,
            engagement_id=str(uuid4()),
            tenant_key="tenant-1",
            auditor_only=False,
            viewer_membership_id=str(uuid4()),
        )

        self.assertEqual(len(connection.args), 2)

    async def test_list_engagement_controls_uses_membership_arg_for_auditor_queries(self) -> None:
        connection = _FetchConnection()
        repo = repository_module.EngagementRepository()

        await repo.list_engagement_controls(
            connection,
            engagement_id=str(uuid4()),
            tenant_key="tenant-1",
            auditor_only=True,
            viewer_membership_id=str(uuid4()),
        )

        self.assertEqual(len(connection.args), 3)
        assert connection.sql is not None
        self.assertIn("g.membership_id = $3::uuid", connection.sql)

    async def test_list_control_evidence_uses_entity_linkage_instead_of_owner_id(self) -> None:
        connection = _FetchConnection()
        repo = repository_module.EngagementRepository()

        await repo.list_control_evidence(
            connection,
            engagement_id=str(uuid4()),
            tenant_key="tenant-1",
            control_id=str(uuid4()),
            auditor_only=True,
            viewer_membership_id=str(uuid4()),
        )

        assert connection.sql is not None
        self.assertNotIn("owner_id", connection.sql)
        self.assertIn("att.entity_type = 'engagement'", connection.sql)
        self.assertIn("att.entity_type = 'control'", connection.sql)

    async def test_auditor_attachment_library_requires_creator_approved_grant(self) -> None:
        attachments_repository_module = import_module("backend.09_attachments.01_attachments.repository")
        connection = _FetchConnection()
        repo = attachments_repository_module.AttachmentRepository()

        await repo.list_attachments(
            connection,
            tenant_key="tenant-1",
            engagement_id=str(uuid4()),
            auditor_only=True,
            viewer_membership_id=str(uuid4()),
        )

        assert connection.sql is not None
        self.assertIn('JOIN "12_engagements"."10_fct_audit_engagements" e', connection.sql)
        self.assertIn("g.created_by = e.created_by", connection.sql)
        self.assertNotIn("OR auditor_access = TRUE", connection.sql)

    async def test_attachment_context_match_query_uses_entity_type_and_entity_id(self) -> None:
        connection = _FetchValConnection()
        engagement_id = str(uuid4())
        control_id = str(uuid4())
        repo = repository_module.EngagementRepository()

        await connection.fetchval(
            """
            SELECT 1 FROM "09_attachments"."01_fct_attachments" 
            WHERE id = $1 AND tenant_key = $2 
              AND (
                    (entity_type = 'engagement' AND entity_id = $3::uuid)
                 OR (entity_type = 'control' AND entity_id = $4::uuid)
              )
            """,
            str(uuid4()),
            "tenant-1",
            engagement_id,
            control_id,
        )

        assert connection.sql is not None
        self.assertNotIn("owner_id", connection.sql)
        self.assertIn("entity_type = 'engagement'", connection.sql)
        self.assertIn("entity_type = 'control'", connection.sql)


if __name__ == "__main__":
    unittest.main()
