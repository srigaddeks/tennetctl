from __future__ import annotations

from importlib import import_module
from pathlib import Path
from socket import socket
import shutil
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import asyncpg
import httpx


application_module = import_module("backend.01_core.application")
settings_module = import_module("backend.00_config.settings")

create_app = application_module.create_app
Settings = settings_module.Settings


class _PostgresTestServer:
    def __init__(self) -> None:
        self._temp_root = Path("backend/90_tests/.tmp")
        self._temp_root.mkdir(parents=True, exist_ok=True)
        self.base_path = Path(tempfile.mkdtemp(prefix="kcontrol-pg-aud-eng-", dir=self._temp_root))
        self.data_path = self.base_path / "data"
        self.port = self._find_free_port()
        self.database_name = "kcontrol_auditor_engagement_test"
        self.database_dsn = f"postgresql://postgres@127.0.0.1:{self.port}/{self.database_name}?sslmode=disable"

    def start(self) -> None:
        subprocess.run(
            [shutil.which("initdb") or "initdb", "-D", str(self.data_path), "-A", "trust", "-U", "postgres", "--locale=C"],
            check=True,
        )
        subprocess.run(
            [shutil.which("pg_ctl") or "pg_ctl", "-D", str(self.data_path), "-o", f"-p {self.port}", "-w", "start"],
            check=True,
        )
        subprocess.run(
            [shutil.which("createdb") or "createdb", "-h", "127.0.0.1", "-p", str(self.port), "-U", "postgres", self.database_name],
            check=True,
        )

    def stop(self) -> None:
        try:
            subprocess.run(
                [shutil.which("pg_ctl") or "pg_ctl", "-D", str(self.data_path), "-m", "immediate", "stop"],
                check=True,
            )
        finally:
            shutil.rmtree(self.base_path, ignore_errors=True)

    @staticmethod
    def _find_free_port() -> int:
        with socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


def _make_settings(database_dsn: str) -> Settings:
    return Settings(
        environment="test",
        app_name="kcontrol-auditor-engagement-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=True,
        database_url=database_dsn,
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-auditor-eng-secret",
        access_token_algorithm="HS256",
        access_token_issuer="kcontrol.test",
        access_token_audience="kcontrol-test-api",
        access_token_ttl_seconds=900,
        refresh_token_ttl_seconds=3600,
        brute_force_window_seconds=900,
        brute_force_max_attempts=5,
        default_tenant_key="default",
        trust_proxy_headers=False,
        trusted_proxy_depth=1,
        migration_directory=Path("backend/01_sql_migrations/01_migrated"),
        otel_enabled=False,
        otel_traces_enabled=False,
        otel_function_trace_enabled=False,
    )


class AuditorEngagementMembershipApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = _PostgresTestServer()
        try:
            cls.postgres.start()
        except subprocess.CalledProcessError as exc:
            raise unittest.SkipTest(f"Local PostgreSQL test cluster could not be initialized in this environment: {exc}") from exc

    @classmethod
    def tearDownClass(cls) -> None:
        cls.postgres.stop()

    async def _reset_schema(self) -> None:
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            await conn.execute('DROP SCHEMA IF EXISTS "12_engagements" CASCADE')
            await conn.execute('DROP SCHEMA IF EXISTS "05_grc_library" CASCADE')
            await conn.execute('DROP SCHEMA IF EXISTS "03_auth_manage" CASCADE')
            await conn.execute('DROP SCHEMA IF EXISTS "01_dev_features" CASCADE')
        finally:
            await conn.close()

    async def asyncSetUp(self) -> None:
        await self._reset_schema()
        self.settings = _make_settings(self.postgres.database_dsn)
        self.app = create_app(self.settings)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )
        for relative_path in (
            "backend/01_sql_migrations/01_migrated/20260402_add-engagement-memberships-foundation.sql",
            "backend/01_sql_migrations/01_migrated/20260402_add-auditor-evidence-request-guardrails.sql",
            "backend/01_sql_migrations/01_migrated/20260402_add-evidence-access-grants.sql",
        ):
            await self._apply_inprogress_migration(relative_path)

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def _apply_inprogress_migration(self, path: str) -> None:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            sql = Path(path).read_text(encoding="utf-8")
            await conn.execute(sql)
        finally:
            await conn.close()

    async def _register_and_login(self, email: str, password: str = "StrongPassword123") -> dict:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": email, "password": password},
        )
        resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": email, "password": password},
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    async def _get_user_id(self, access_token: str) -> str:
        resp = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()["user_id"]

    async def _grant_super_admin(self, user_id: str) -> None:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        now = datetime.now(UTC).replace(tzinfo=None)
        try:
            group_id = await conn.fetchval(
                """
                SELECT id
                FROM "03_auth_manage"."17_fct_user_groups"
                WHERE code = 'platform_super_admin' AND tenant_key = 'default'
                """
            )
            await conn.execute(
                """
                INSERT INTO "03_auth_manage"."18_lnk_group_memberships" (
                    id, group_id, user_id, membership_status, effective_from, effective_to,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES ($1, $2, $3, 'active', $4, NULL,
                        TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
                        $4, $4, NULL, NULL, NULL, NULL)
                ON CONFLICT DO NOTHING
                """,
                str(uuid4()),
                group_id,
                user_id,
                now,
            )
        finally:
            await conn.close()

    def _auth_headers(self, tokens: dict) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    async def _seed_engagement(
        self,
        *,
        member_user_id: str | None = None,
        membership_status: str = "active",
        membership_expires_at: datetime | None = None,
        membership_is_active: bool = True,
        return_context: bool = False,
    ) -> str | dict[str, str | None]:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        now = datetime.now(UTC).replace(tzinfo=None)
        try:
            org_type_code = await conn.fetchval('SELECT code FROM "03_auth_manage"."28_dim_org_types" ORDER BY code LIMIT 1')
            workspace_type_code = await conn.fetchval('SELECT code FROM "03_auth_manage"."33_dim_workspace_types" ORDER BY code LIMIT 1')
            framework_type_code = await conn.fetchval('SELECT code FROM "05_grc_library"."02_dim_framework_types" ORDER BY code LIMIT 1')
            framework_category_code = await conn.fetchval('SELECT code FROM "05_grc_library"."03_dim_framework_categories" ORDER BY code LIMIT 1')
            control_category_code = await conn.fetchval('SELECT code FROM "05_grc_library"."04_dim_control_categories" ORDER BY code LIMIT 1')

            org_id = str(uuid4())
            workspace_id = str(uuid4())
            framework_id = str(uuid4())
            version_id = str(uuid4())
            deployment_id = str(uuid4())
            engagement_id = str(uuid4())

            await conn.execute(
                """
                INSERT INTO "03_auth_manage"."29_fct_orgs" (
                    id, tenant_key, org_type_code, code, name, description,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at
                ) VALUES ($1, 'default', $2, $3, 'Audit Org', 'Audit Org',
                          TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $4, $4)
                """,
                org_id, org_type_code, f"org_{org_id[:8]}", now,
            )
            await conn.execute(
                """
                INSERT INTO "03_auth_manage"."34_fct_workspaces" (
                    id, org_id, workspace_type_code, product_id, code, name, description,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, NULL, $4, 'Audit Workspace', 'Audit Workspace',
                          TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $5, $5)
                """,
                workspace_id, org_id, workspace_type_code, f"ws_{workspace_id[:8]}", now,
            )
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."10_fct_frameworks" (
                    id, tenant_key, framework_code, framework_type_code, framework_category_code,
                    scope_org_id, scope_workspace_id, approval_status, is_marketplace_visible,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at
                ) VALUES ($1, 'default', $2, $3, $4, $5, $6, 'approved', FALSE,
                          TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $7, $7)
                """,
                framework_id, f"FW_{framework_id[:8]}", framework_type_code, framework_category_code, org_id, workspace_id, now,
            )
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."11_fct_framework_versions" (
                    id, framework_id, version_code, change_severity, lifecycle_state, control_count,
                    previous_version_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at
                ) VALUES ($1, $2, '1.0', 'minor', 'published', 0,
                          NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $3, $3)
                """,
                version_id, framework_id, now,
            )
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."16_fct_framework_deployments" (
                    id, tenant_key, org_id, framework_id, deployed_version_id,
                    deployment_status, workspace_id, is_active, created_at, updated_at
                ) VALUES ($1, 'default', $2, $3, $4, 'active', $5, TRUE, $6, $6)
                """,
                deployment_id, org_id, framework_id, version_id, workspace_id, now,
            )
            control_id = str(uuid4())
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."13_fct_controls" (
                    id, framework_id, requirement_id, tenant_key, control_code, control_category_code,
                    criticality_code, control_type, automation_potential, sort_order,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at
                ) VALUES ($1, $2, NULL, 'default', 'CC1.1', $3,
                          'medium', 'preventive', 'manual', 1,
                          TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $4, $4)
                """,
                control_id, framework_id, control_category_code, now,
            )
            await conn.execute(
                """
                INSERT INTO "12_engagements"."10_fct_audit_engagements" (
                    id, tenant_key, org_id, engagement_code, framework_id, framework_deployment_id,
                    status_code, target_completion_date, is_active, is_deleted, created_at, updated_at
                ) VALUES ($1, 'default', $2, $3, $4, $5, 'active', NULL, TRUE, FALSE, $6, $6)
                """,
                engagement_id, org_id, f"ENG-{engagement_id[:6]}", framework_id, deployment_id, now,
            )
            await conn.execute(
                """
                INSERT INTO "12_engagements"."22_dtl_engagement_properties" (
                    id, engagement_id, property_key, property_value, updated_at
                ) VALUES
                    ($1, $2, 'engagement_name', 'FY26 External Audit', $3),
                    ($4, $2, 'auditor_firm', 'Audit Co', $3)
                """,
                str(uuid4()), engagement_id, now, str(uuid4()),
            )

            membership_id: str | None = None
            if member_user_id:
                membership_id = str(uuid4())
                await conn.execute(
                    """
                    INSERT INTO "12_engagements"."12_lnk_engagement_memberships" (
                        id, tenant_key, engagement_id, org_id, workspace_id, user_id, external_email,
                        membership_type_code, status_code, joined_at, expires_at,
                        is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                        created_at, updated_at, created_by, updated_by
                    ) VALUES (
                        $1, 'default', $2, $3, $4, $5, NULL,
                        'external_auditor', $6, $7, $8,
                        $9, FALSE, FALSE, FALSE, FALSE, FALSE,
                        $7, $7, $5, $5
                    )
                    """,
                    membership_id,
                    engagement_id,
                    org_id,
                    workspace_id,
                    member_user_id,
                    membership_status,
                    now,
                    membership_expires_at,
                    membership_is_active,
                )

            if return_context:
                return {
                    "engagement_id": engagement_id,
                    "org_id": org_id,
                    "workspace_id": workspace_id,
                    "framework_id": framework_id,
                    "control_id": control_id,
                    "membership_id": membership_id,
                }
            return engagement_id
        finally:
            await conn.close()

    async def _seed_membership(
        self,
        *,
        engagement_id: str,
        org_id: str,
        workspace_id: str,
        user_id: str,
        membership_status: str = "active",
        membership_type_code: str = "external_auditor",
        membership_expires_at: datetime | None = None,
        membership_is_active: bool = True,
    ) -> str:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        now = datetime.now(UTC).replace(tzinfo=None)
        membership_id = str(uuid4())
        try:
            await conn.execute(
                """
                INSERT INTO "12_engagements"."12_lnk_engagement_memberships" (
                    id, tenant_key, engagement_id, org_id, workspace_id, user_id, external_email,
                    membership_type_code, status_code, joined_at, expires_at,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by
                ) VALUES (
                    $1, 'default', $2, $3, $4, $5, NULL,
                    $6, $7, $8, $9,
                    $10, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $8, $8, $5, $5
                )
                """,
                membership_id,
                engagement_id,
                org_id,
                workspace_id,
                user_id,
                membership_type_code,
                membership_status,
                now,
                membership_expires_at,
                membership_is_active,
            )
            return membership_id
        finally:
            await conn.close()

    async def _seed_control_attachment(
        self,
        *,
        control_id: str,
        uploaded_by: str,
        auditor_access: bool,
        filename: str,
    ) -> str:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        now = datetime.now(UTC).replace(tzinfo=None)
        attachment_id = str(uuid4())
        try:
            await conn.execute(
                """
                INSERT INTO "09_attachments"."01_fct_attachments" (
                    id, tenant_key, entity_type, entity_id, uploaded_by, original_filename,
                    storage_key, storage_provider, storage_bucket, storage_url,
                    content_type, file_size_bytes, checksum_sha256,
                    is_deleted, virus_scan_status, description, auditor_access,
                    published_for_audit_by, published_for_audit_at,
                    created_at, updated_at
                ) VALUES (
                    $1::uuid, 'default', 'control', $2::uuid, $3::uuid, $4,
                    $5, 's3', 'test-bucket', NULL,
                    'application/pdf', 128, repeat('a', 64),
                    FALSE, 'clean', 'seeded evidence', $6,
                    CASE WHEN $6 THEN $3::uuid ELSE NULL END,
                    CASE WHEN $6 THEN $7 ELSE NULL END,
                    $7, $7
                )
                """,
                attachment_id,
                control_id,
                uploaded_by,
                filename,
                f"default/control/{control_id}/{attachment_id}/{filename}",
                auditor_access,
                now,
            )
            return attachment_id
        finally:
            await conn.close()

    async def _seed_access_token(
        self,
        *,
        engagement_id: str,
        auditor_user_id: str,
        auditor_email: str,
        expires_at: datetime | None = None,
    ) -> str:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        token_id = str(uuid4())
        token_expiry = expires_at or (datetime.now(UTC).replace(tzinfo=None) + timedelta(days=7))
        try:
            await conn.execute(
                """
                INSERT INTO "12_engagements"."11_fct_audit_access_tokens" (
                    id, engagement_id, auditor_user_id, auditor_email, token_hash,
                    expires_at, last_accessed_at, is_revoked, revoked_at, revoked_by, created_at
                ) VALUES (
                    $1::uuid, $2::uuid, $3::uuid, $4, $5,
                    $6, NULL, FALSE, NULL, NULL, NOW()
                )
                """,
                token_id,
                engagement_id,
                auditor_user_id,
                auditor_email,
                f"seed-token-{token_id}",
                token_expiry,
            )
            return token_id
        finally:
            await conn.close()

    async def _seed_evidence_grant(
        self,
        *,
        engagement_id: str,
        membership_id: str,
        attachment_id: str,
        granted_by: str,
    ) -> None:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        now = datetime.now(UTC).replace(tzinfo=None)
        try:
            await conn.execute(
                """
                INSERT INTO "12_engagements"."13_lnk_evidence_access_grants" (
                    id, tenant_key, engagement_id, request_id, membership_id, attachment_id,
                    granted_at, expires_at, revoked_at, revoked_by,
                    is_active, is_deleted, created_at, updated_at, created_by, updated_by
                ) VALUES (
                    $1::uuid, 'default', $2::uuid, NULL, $3::uuid, $4::uuid,
                    $5, NULL, NULL, NULL,
                    TRUE, FALSE, $5, $5, $6::uuid, $6::uuid
                )
                """,
                str(uuid4()),
                engagement_id,
                membership_id,
                attachment_id,
                now,
                granted_by,
            )
        finally:
            await conn.close()

    async def _get_request_row(self, *, request_id: str) -> asyncpg.Record:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            row = await conn.fetchrow(
                """
                SELECT id, request_status, attachment_id, fulfilled_by, fulfilled_at, response_notes
                FROM "12_engagements"."20_trx_auditor_requests"
                WHERE id = $1::uuid
                """,
                request_id,
            )
            assert row is not None
            return row
        finally:
            await conn.close()

    async def _set_request_fulfilled_at(self, *, request_id: str, fulfilled_at: datetime) -> None:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            await conn.execute(
                """
                UPDATE "12_engagements"."20_trx_auditor_requests"
                SET fulfilled_at = $2
                WHERE id = $1::uuid
                """,
                request_id,
                fulfilled_at,
            )
        finally:
            await conn.close()

    async def _fetch_disable_state(self, *, user_id: str) -> dict[str, int]:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            row = await conn.fetchrow(
                """
                SELECT
                    (SELECT COUNT(*)::int
                     FROM "03_auth_manage"."10_trx_auth_sessions"
                     WHERE user_id = $1::uuid AND revoked_at IS NOT NULL) AS revoked_sessions,
                    (SELECT COUNT(*)::int
                     FROM "12_engagements"."12_lnk_engagement_memberships"
                     WHERE user_id = $1::uuid AND is_active = FALSE AND status_code = 'revoked') AS revoked_memberships,
                    (SELECT COUNT(*)::int
                     FROM "12_engagements"."13_lnk_evidence_access_grants" g
                     JOIN "12_engagements"."12_lnk_engagement_memberships" m
                       ON m.id = g.membership_id
                     WHERE m.user_id = $1::uuid
                       AND g.revoked_at IS NOT NULL
                       AND g.is_active = FALSE) AS revoked_grants
                """,
                user_id,
            )
            return {
                "revoked_sessions": row["revoked_sessions"],
                "revoked_memberships": row["revoked_memberships"],
                "revoked_grants": row["revoked_grants"],
            }
        finally:
            await conn.close()

    async def _set_user_suspended(self, user_id: str) -> None:
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            await conn.execute(
                """
                UPDATE "03_auth_manage"."03_fct_users"
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1::uuid
                """,
                user_id,
            )
        finally:
            await conn.close()

    async def test_member_can_see_assigned_engagement_and_non_member_cannot(self) -> None:
        member_tokens = await self._register_and_login("member@example.com")
        outsider_tokens = await self._register_and_login("outsider@example.com")
        member_user_id = await self._get_user_id(member_tokens["access_token"])

        engagement_id = await self._seed_engagement(member_user_id=member_user_id)

        member_portfolio = await self.client.get(
            "/api/v1/engagements/my-engagements",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(member_portfolio.status_code, 200)
        portfolio_items = member_portfolio.json()
        self.assertEqual(len(portfolio_items), 1)
        self.assertEqual(portfolio_items[0]["id"], engagement_id)
        self.assertEqual(portfolio_items[0]["workspace_name"], "Audit Workspace")

        outsider_portfolio = await self.client.get(
            "/api/v1/engagements/my-engagements",
            headers=self._auth_headers(outsider_tokens),
        )
        self.assertEqual(outsider_portfolio.status_code, 200)
        self.assertEqual(outsider_portfolio.json(), [])

        member_detail = await self.client.get(
            f"/api/v1/engagements/{engagement_id}",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(member_detail.status_code, 200)
        self.assertEqual(member_detail.json()["id"], engagement_id)

        outsider_detail = await self.client.get(
            f"/api/v1/engagements/{engagement_id}",
            headers=self._auth_headers(outsider_tokens),
        )
        self.assertEqual(outsider_detail.status_code, 404)

    async def test_pending_expired_revoked_and_suspended_users_are_denied(self) -> None:
        pending_tokens = await self._register_and_login("pending@example.com")
        expired_tokens = await self._register_and_login("expired@example.com")
        revoked_tokens = await self._register_and_login("revoked@example.com")
        suspended_tokens = await self._register_and_login("suspended@example.com")

        pending_user_id = await self._get_user_id(pending_tokens["access_token"])
        expired_user_id = await self._get_user_id(expired_tokens["access_token"])
        revoked_user_id = await self._get_user_id(revoked_tokens["access_token"])
        suspended_user_id = await self._get_user_id(suspended_tokens["access_token"])

        engagement_id = await self._seed_engagement(member_user_id=pending_user_id, membership_status="pending")
        await self._seed_engagement(
            member_user_id=expired_user_id,
            membership_status="active",
            membership_expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1),
        )
        await self._seed_engagement(
            member_user_id=revoked_user_id,
            membership_status="revoked",
            membership_is_active=False,
        )
        await self._seed_engagement(member_user_id=suspended_user_id)
        await self._set_user_suspended(suspended_user_id)

        for tokens in (pending_tokens, expired_tokens, revoked_tokens):
            portfolio = await self.client.get(
                "/api/v1/engagements/my-engagements",
                headers=self._auth_headers(tokens),
            )
            self.assertEqual(portfolio.status_code, 200)
            self.assertEqual(portfolio.json(), [])

            detail = await self.client.get(
                f"/api/v1/engagements/{engagement_id}",
                headers=self._auth_headers(tokens),
            )
            self.assertEqual(detail.status_code, 404)

        suspended_portfolio = await self.client.get(
            "/api/v1/engagements/my-engagements",
            headers=self._auth_headers(suspended_tokens),
        )
        self.assertEqual(suspended_portfolio.status_code, 403)

        suspended_detail = await self.client.get(
            f"/api/v1/engagements/{engagement_id}",
            headers=self._auth_headers(suspended_tokens),
        )
        self.assertEqual(suspended_detail.status_code, 403)

    async def test_member_sees_controls_but_only_published_or_granted_evidence(self) -> None:
        member_tokens = await self._register_and_login("evidence-member@example.com")
        outsider_tokens = await self._register_and_login("evidence-outsider@example.com")
        member_user_id = await self._get_user_id(member_tokens["access_token"])

        context = await self._seed_engagement(
            member_user_id=member_user_id,
            return_context=True,
        )
        engagement_id = str(context["engagement_id"])
        control_id = str(context["control_id"])
        membership_id = str(context["membership_id"])

        public_attachment_id = await self._seed_control_attachment(
            control_id=control_id,
            uploaded_by=member_user_id,
            auditor_access=True,
            filename="public-evidence.pdf",
        )
        private_attachment_id = await self._seed_control_attachment(
            control_id=control_id,
            uploaded_by=member_user_id,
            auditor_access=False,
            filename="private-evidence.pdf",
        )

        controls_before = await self.client.get(
            f"/api/v1/engagements/{engagement_id}/controls",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(controls_before.status_code, 200)
        control_rows_before = controls_before.json()
        self.assertEqual(len(control_rows_before), 1)
        self.assertEqual(control_rows_before[0]["evidence_count"], 1)

        attachments_before = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(attachments_before.status_code, 200)
        payload_before = attachments_before.json()
        self.assertEqual(payload_before["total"], 1)
        self.assertEqual([item["id"] for item in payload_before["items"]], [public_attachment_id])

        outsider_attachments = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(outsider_tokens),
        )
        self.assertEqual(outsider_attachments.status_code, 403)

        await self._seed_evidence_grant(
            engagement_id=engagement_id,
            membership_id=membership_id,
            attachment_id=private_attachment_id,
            granted_by=member_user_id,
        )

        controls_after = await self.client.get(
            f"/api/v1/engagements/{engagement_id}/controls",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(controls_after.status_code, 200)
        control_rows_after = controls_after.json()
        self.assertEqual(control_rows_after[0]["evidence_count"], 2)

        attachments_after = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(attachments_after.status_code, 200)
        payload_after = attachments_after.json()
        self.assertEqual(payload_after["total"], 2)
        self.assertEqual(
            {item["id"] for item in payload_after["items"]},
            {public_attachment_id, private_attachment_id},
        )

    async def test_evidence_request_can_be_created_fulfilled_and_revoked(self) -> None:
        admin_tokens = await self._register_and_login("evidence-admin@example.com")
        auditor_tokens = await self._register_and_login("request-auditor@example.com")
        admin_user_id = await self._get_user_id(admin_tokens["access_token"])
        auditor_user_id = await self._get_user_id(auditor_tokens["access_token"])
        await self._grant_super_admin(admin_user_id)

        context = await self._seed_engagement(
            member_user_id=auditor_user_id,
            return_context=True,
        )
        engagement_id = str(context["engagement_id"])
        control_id = str(context["control_id"])
        membership_id = str(context["membership_id"])
        await self._seed_access_token(
            engagement_id=engagement_id,
            auditor_user_id=auditor_user_id,
            auditor_email="request-auditor@example.com",
        )

        private_attachment_id = await self._seed_control_attachment(
            control_id=control_id,
            uploaded_by=admin_user_id,
            auditor_access=False,
            filename="approval-only.pdf",
        )

        create_request = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/controls/{control_id}/request-docs",
            headers=self._auth_headers(auditor_tokens),
            json={"description": "Need the operating evidence for walkthrough."},
        )
        self.assertEqual(create_request.status_code, 200)
        request_id = create_request.json()["id"]

        before_approval = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(auditor_tokens),
        )
        self.assertEqual(before_approval.status_code, 200)
        self.assertEqual(before_approval.json()["total"], 0)

        fulfill = await self.client.patch(
            f"/api/v1/engagements/{engagement_id}/requests/{request_id}",
            headers=self._auth_headers(admin_tokens),
            json={
                "action": "fulfill",
                "attachment_id": private_attachment_id,
                "response_notes": "Approved for this engagement reviewer.",
            },
        )
        self.assertEqual(fulfill.status_code, 200)
        self.assertEqual(fulfill.json()["request_status"], "fulfilled")

        request_row = await self._get_request_row(request_id=request_id)
        self.assertEqual(str(request_row["attachment_id"]), private_attachment_id)
        self.assertEqual(str(request_row["fulfilled_by"]), admin_user_id)
        self.assertEqual(request_row["request_status"], "fulfilled")

        after_approval = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(auditor_tokens),
        )
        self.assertEqual(after_approval.status_code, 200)
        self.assertEqual(after_approval.json()["total"], 1)
        self.assertEqual(after_approval.json()["items"][0]["id"], private_attachment_id)

        revoke = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/requests/{request_id}/revoke",
            headers=self._auth_headers(admin_tokens),
            json={"response_notes": "Access window closed."},
        )
        self.assertEqual(revoke.status_code, 200)
        self.assertEqual(revoke.json()["request_status"], "dismissed")

        after_revoke = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(auditor_tokens),
        )
        self.assertEqual(after_revoke.status_code, 200)
        self.assertEqual(after_revoke.json()["total"], 0)

    async def test_duplicate_and_rejected_evidence_requests_are_blocked(self) -> None:
        admin_tokens = await self._register_and_login("review-admin@example.com")
        auditor_tokens = await self._register_and_login("cooldown-auditor@example.com")
        admin_user_id = await self._get_user_id(admin_tokens["access_token"])
        auditor_user_id = await self._get_user_id(auditor_tokens["access_token"])
        await self._grant_super_admin(admin_user_id)

        context = await self._seed_engagement(
            member_user_id=auditor_user_id,
            return_context=True,
        )
        engagement_id = str(context["engagement_id"])
        control_id = str(context["control_id"])
        await self._seed_access_token(
            engagement_id=engagement_id,
            auditor_user_id=auditor_user_id,
            auditor_email="cooldown-auditor@example.com",
        )

        create_request = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/controls/{control_id}/request-docs",
            headers=self._auth_headers(auditor_tokens),
            json={"description": "Need sample evidence."},
        )
        self.assertEqual(create_request.status_code, 200)
        request_id = create_request.json()["id"]

        duplicate_open = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/controls/{control_id}/request-docs",
            headers=self._auth_headers(auditor_tokens),
            json={"description": "Need sample evidence."},
        )
        self.assertEqual(duplicate_open.status_code, 409)

        dismiss = await self.client.patch(
            f"/api/v1/engagements/{engagement_id}/requests/{request_id}",
            headers=self._auth_headers(admin_tokens),
            json={"action": "dismiss", "response_notes": "Please narrow the request."},
        )
        self.assertEqual(dismiss.status_code, 200)
        self.assertEqual(dismiss.json()["request_status"], "dismissed")

        immediate_retry = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/controls/{control_id}/request-docs",
            headers=self._auth_headers(auditor_tokens),
            json={"description": "Need a narrower sample evidence set."},
        )
        self.assertEqual(immediate_retry.status_code, 409)
        self.assertIn("Please wait", immediate_retry.text)

        await self._set_request_fulfilled_at(
            request_id=request_id,
            fulfilled_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1),
        )

        same_reason_retry = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/controls/{control_id}/request-docs",
            headers=self._auth_headers(auditor_tokens),
            json={"description": "Need sample evidence."},
        )
        self.assertEqual(same_reason_retry.status_code, 409)
        self.assertIn("fresh justification", same_reason_retry.text)

    async def test_engagement_task_creation_requires_participant_assignee_and_in_scope_entity(self) -> None:
        reporter_tokens = await self._register_and_login("task-reporter@example.com")
        participant_tokens = await self._register_and_login("task-participant@example.com")
        outsider_tokens = await self._register_and_login("task-outsider@example.com")

        reporter_user_id = await self._get_user_id(reporter_tokens["access_token"])
        participant_user_id = await self._get_user_id(participant_tokens["access_token"])
        outsider_user_id = await self._get_user_id(outsider_tokens["access_token"])

        context = await self._seed_engagement(
            member_user_id=reporter_user_id,
            return_context=True,
        )
        engagement_id = str(context["engagement_id"])
        org_id = str(context["org_id"])
        workspace_id = str(context["workspace_id"])
        control_id = str(context["control_id"])

        await self._seed_membership(
            engagement_id=engagement_id,
            org_id=org_id,
            workspace_id=workspace_id,
            user_id=participant_user_id,
            membership_type_code="contributor",
        )

        participants = await self.client.get(
            f"/api/v1/engagements/{engagement_id}/participants",
            headers=self._auth_headers(reporter_tokens),
        )
        self.assertEqual(participants.status_code, 200)
        participant_ids = {item["user_id"] for item in participants.json()}
        self.assertIn(reporter_user_id, participant_ids)
        self.assertIn(participant_user_id, participant_ids)
        self.assertNotIn(outsider_user_id, participant_ids)

        valid_task = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/tasks",
            headers=self._auth_headers(reporter_tokens),
            json={
                "task_type_code": "evidence_request",
                "priority_code": "medium",
                "entity_type": "control",
                "entity_id": control_id,
                "assignee_user_id": participant_user_id,
                "title": "Collect reviewer evidence",
                "description": "Upload the approved evidence package for the auditor.",
            },
        )
        self.assertEqual(valid_task.status_code, 201)
        self.assertEqual(valid_task.json()["assignee_user_id"], participant_user_id)
        self.assertEqual(valid_task.json()["entity_id"], control_id)

        outsider_assignment = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/tasks",
            headers=self._auth_headers(reporter_tokens),
            json={
                "task_type_code": "evidence_request",
                "priority_code": "medium",
                "entity_type": "control",
                "entity_id": control_id,
                "assignee_user_id": outsider_user_id,
                "title": "Invalid assignment",
            },
        )
        self.assertEqual(outsider_assignment.status_code, 400)
        self.assertIn("active participant", outsider_assignment.text)

        out_of_scope_entity = await self.client.post(
            f"/api/v1/engagements/{engagement_id}/tasks",
            headers=self._auth_headers(reporter_tokens),
            json={
                "task_type_code": "evidence_request",
                "priority_code": "medium",
                "entity_type": "control",
                "entity_id": str(uuid4()),
                "title": "Out of scope control task",
            },
        )
        self.assertEqual(out_of_scope_entity.status_code, 400)
        self.assertIn("must belong to the selected engagement", out_of_scope_entity.text)

    async def test_admin_disable_user_revokes_sessions_memberships_and_evidence_grants(self) -> None:
        admin_tokens = await self._register_and_login("platform-admin@example.com")
        member_tokens = await self._register_and_login("suspend-member@example.com")
        admin_user_id = await self._get_user_id(admin_tokens["access_token"])
        member_user_id = await self._get_user_id(member_tokens["access_token"])
        await self._grant_super_admin(admin_user_id)

        context = await self._seed_engagement(
            member_user_id=member_user_id,
            return_context=True,
        )
        engagement_id = str(context["engagement_id"])
        control_id = str(context["control_id"])
        membership_id = str(context["membership_id"])

        private_attachment_id = await self._seed_control_attachment(
            control_id=control_id,
            uploaded_by=member_user_id,
            auditor_access=False,
            filename="suspend-private-evidence.pdf",
        )
        await self._seed_evidence_grant(
            engagement_id=engagement_id,
            membership_id=membership_id,
            attachment_id=private_attachment_id,
            granted_by=admin_user_id,
        )

        before_disable = await self.client.get(
            f"/api/v1/attachments?engagement_id={engagement_id}",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(before_disable.status_code, 200)
        self.assertEqual(before_disable.json()["total"], 1)

        disable_response = await self.client.patch(
            f"/api/v1/am/admin/users/{member_user_id}/disable",
            headers=self._auth_headers(admin_tokens),
        )
        self.assertEqual(disable_response.status_code, 200)
        self.assertTrue(disable_response.json()["is_disabled"])

        post_disable_portfolio = await self.client.get(
            "/api/v1/engagements/my-engagements",
            headers=self._auth_headers(member_tokens),
        )
        self.assertEqual(post_disable_portfolio.status_code, 401)

        refresh_response = await self.client.post(
            "/api/v1/auth/local/refresh",
            json={"refresh_token": member_tokens["refresh_token"]},
        )
        self.assertEqual(refresh_response.status_code, 401)

        state = await self._fetch_disable_state(user_id=member_user_id)
        self.assertGreaterEqual(state["revoked_sessions"], 1)
        self.assertEqual(state["revoked_memberships"], 1)
        self.assertEqual(state["revoked_grants"], 1)


if __name__ == "__main__":
    unittest.main()
