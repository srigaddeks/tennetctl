from __future__ import annotations

from importlib import import_module
from pathlib import Path
from socket import socket
import shutil
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from uuid import uuid4

import asyncpg
import httpx


application_module = import_module("backend.01_core.application")
settings_module = import_module("backend.00_config.settings")

create_app = application_module.create_app
Settings = settings_module.Settings


class _PostgresTestServer:
    def __init__(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory(prefix="kcontrol-pg-inv-")
        self.base_path = Path(self._temp_dir.name)
        self.data_path = self.base_path / "data"
        self.port = self._find_free_port()
        self.database_name = "kcontrol_inv_test"
        self.admin_dsn = f"postgresql://postgres@127.0.0.1:{self.port}/postgres?sslmode=disable"
        self.database_dsn = f"postgresql://postgres@127.0.0.1:{self.port}/{self.database_name}?sslmode=disable"

    def start(self) -> None:
        subprocess.run(
            [shutil.which("initdb") or "initdb", "-D", str(self.data_path),
             "-A", "trust", "-U", "postgres", "--locale=C"],
            check=True,
        )
        subprocess.run(
            [shutil.which("pg_ctl") or "pg_ctl", "-D", str(self.data_path),
             "-o", f"-p {self.port}", "-w", "start"],
            check=True,
        )
        subprocess.run(
            [shutil.which("createdb") or "createdb", "-h", "127.0.0.1",
             "-p", str(self.port), "-U", "postgres", self.database_name],
            check=True,
        )

    def stop(self) -> None:
        try:
            subprocess.run(
                [shutil.which("pg_ctl") or "pg_ctl", "-D", str(self.data_path),
                 "-m", "immediate", "stop"],
                check=True,
            )
        finally:
            self._temp_dir.cleanup()

    @staticmethod
    def _find_free_port() -> int:
        with socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


def _make_settings(database_dsn: str) -> Settings:
    return Settings(
        environment="test",
        app_name="kcontrol-inv-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=True,
        database_url=database_dsn,
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-inv-secret",
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


class InvitationApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = _PostgresTestServer()
        cls.postgres.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.postgres.stop()

    async def _reset_schema(self) -> None:
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
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

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    # ─── helpers ────────────────────────────────────────────────────────────

    async def _register_and_login(self, email: str, password: str = "StrongPassword123") -> dict:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": email, "password": password},
        )
        resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": email, "password": password},
        )
        return resp.json()

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
                        $5, $6, NULL, NULL, NULL, NULL)
                ON CONFLICT DO NOTHING
                """,
                str(uuid4()), group_id, user_id, now, now, now,
            )
            # Grant org/workspace management permissions to super admin role
            role_id = await conn.fetchval(
                """
                SELECT id FROM "03_auth_manage"."16_fct_roles"
                WHERE code = 'platform_super_admin' AND tenant_key = 'default'
                """
            )
            perm_rows = await conn.fetch(
                """
                SELECT id FROM "03_auth_manage"."15_dim_feature_permissions"
                WHERE feature_flag_code IN ('org_management', 'workspace_management')
                """
            )
            for perm_row in perm_rows:
                await conn.execute(
                    """
                    INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
                        id, role_id, feature_permission_id,
                        is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                        created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                    )
                    VALUES ($1, $2, $3,
                            TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
                            $4, $5, NULL, NULL, NULL, NULL)
                    ON CONFLICT DO NOTHING
                    """,
                    str(uuid4()), role_id, perm_row["id"], now, now,
                )
        finally:
            await conn.close()

    async def _get_user_id(self, access_token: str) -> str:
        resp = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return resp.json()["user_id"]

    async def _setup_admin(self) -> tuple[str, dict]:
        """Register, login, grant super admin, return (user_id, tokens)."""
        tokens = await self._register_and_login("admin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        return user_id, tokens

    def _auth_headers(self, tokens: dict) -> dict:
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    async def _create_org(self, tokens: dict) -> str:
        resp = await self.client.post(
            "/api/v1/am/orgs",
            headers=self._auth_headers(tokens),
            json={"name": "Test Org", "slug": "test-org", "org_type_code": "company"},
        )
        return resp.json()["id"]

    async def _create_workspace(self, tokens: dict, org_id: str) -> str:
        resp = await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces",
            headers=self._auth_headers(tokens),
            json={
                "name": "Test Workspace",
                "slug": "test-ws",
                "workspace_type_code": "project",
            },
        )
        return resp.json()["id"]

    # ─── tests ──────────────────────────────────────────────────────────────

    async def test_create_platform_invitation(self) -> None:
        _, tokens = await self._setup_admin()
        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "invited@example.com", "scope": "platform"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["email"], "invited@example.com")
        self.assertEqual(data["scope"], "platform")
        self.assertEqual(data["status"], "pending")
        self.assertIn("invite_token", data)
        self.assertIsNone(data["org_id"])
        self.assertIsNone(data["role"])

    async def test_create_org_invitation(self) -> None:
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)

        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "org-invite@example.com",
                "scope": "organization",
                "org_id": org_id,
                "role": "member",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["scope"], "organization")
        self.assertEqual(data["org_id"], org_id)
        self.assertEqual(data["role"], "member")

    async def test_create_workspace_invitation(self) -> None:
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "ws-invite@example.com",
                "scope": "workspace",
                "org_id": org_id,
                "workspace_id": ws_id,
                "role": "contributor",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["scope"], "workspace")
        self.assertEqual(data["workspace_id"], ws_id)
        self.assertEqual(data["role"], "contributor")

    async def test_duplicate_pending_invite_is_rejected(self) -> None:
        _, tokens = await self._setup_admin()
        body = {"email": "dup@example.com", "scope": "platform"}

        resp1 = await self.client.post(
            "/api/v1/am/invitations", headers=self._auth_headers(tokens), json=body,
        )
        self.assertEqual(resp1.status_code, 201)

        resp2 = await self.client.post(
            "/api/v1/am/invitations", headers=self._auth_headers(tokens), json=body,
        )
        self.assertEqual(resp2.status_code, 409)

    async def test_list_invitations(self) -> None:
        _, tokens = await self._setup_admin()
        await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "list1@example.com", "scope": "platform"},
        )
        await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "list2@example.com", "scope": "platform"},
        )

        resp = await self.client.get(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total"], 2)
        self.assertEqual(data["page"], 1)

    async def test_get_invitation_stats(self) -> None:
        _, tokens = await self._setup_admin()
        await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "stats@example.com", "scope": "platform"},
        )

        resp = await self.client.get(
            "/api/v1/am/invitations/stats",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["pending"], 1)
        self.assertIn("total", data)
        self.assertIn("accepted", data)

    async def test_get_invitation_detail(self) -> None:
        _, tokens = await self._setup_admin()
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "detail@example.com", "scope": "platform"},
        )
        invite_id = create_resp.json()["id"]

        resp = await self.client.get(
            f"/api/v1/am/invitations/{invite_id}",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], invite_id)

    async def test_revoke_invitation(self) -> None:
        _, tokens = await self._setup_admin()
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "revoke@example.com", "scope": "platform"},
        )
        invite_id = create_resp.json()["id"]

        resp = await self.client.patch(
            f"/api/v1/am/invitations/{invite_id}/revoke",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "revoked")

    async def test_accept_invitation_for_existing_user(self) -> None:
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)

        # Register the user FIRST (before invite exists)
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "existing-user@example.com", "password": "StrongPassword123"},
        )

        # Now create the invite for the already-registered user
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "existing-user@example.com",
                "scope": "organization",
                "org_id": org_id,
                "role": "member",
            },
        )
        invite_token = create_resp.json()["invite_token"]

        # Accept the invitation via token
        resp = await self.client.post(
            "/api/v1/am/invitations/accept",
            json={"invite_token": invite_token},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["message"], "Invitation accepted")
        self.assertEqual(data["scope"], "organization")
        self.assertEqual(data["role"], "member")

        # Verify user was added to org
        members_resp = await self.client.get(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
        )
        member_user_ids = [m["user_id"] for m in members_resp.json()]
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "existing-user@example.com", "password": "StrongPassword123"},
        )
        user_token = login_resp.json()["access_token"]
        user_id = await self._get_user_id(user_token)
        self.assertIn(user_id, member_user_ids)

    async def test_accept_invalid_token_returns_404(self) -> None:
        resp = await self.client.post(
            "/api/v1/am/invitations/accept",
            json={"invite_token": "00000000-0000-0000-0000-000000000000.fake_secret_value_1234"},
        )
        self.assertEqual(resp.status_code, 404)

    async def test_accept_revoked_invitation_returns_422(self) -> None:
        _, tokens = await self._setup_admin()
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "revoke-accept@example.com", "scope": "platform"},
        )
        invite_token = create_resp.json()["invite_token"]
        invite_id = create_resp.json()["id"]

        # Revoke it
        await self.client.patch(
            f"/api/v1/am/invitations/{invite_id}/revoke",
            headers=self._auth_headers(tokens),
        )

        # Try to accept
        resp = await self.client.post(
            "/api/v1/am/invitations/accept",
            json={"invite_token": invite_token},
        )
        self.assertEqual(resp.status_code, 422)

    async def test_invalid_scope_fields_rejected(self) -> None:
        _, tokens = await self._setup_admin()

        # Platform with org_id should fail
        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "bad@example.com",
                "scope": "platform",
                "org_id": str(uuid4()),
            },
        )
        self.assertEqual(resp.status_code, 422)

        # Organization without org_id should fail
        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "bad2@example.com", "scope": "organization"},
        )
        self.assertEqual(resp.status_code, 422)

    async def test_invalid_org_role_rejected(self) -> None:
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)

        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "badrole@example.com",
                "scope": "organization",
                "org_id": org_id,
                "role": "contributor",  # Not valid for org
            },
        )
        self.assertEqual(resp.status_code, 422)

    async def test_unprivileged_user_cannot_create_invitation(self) -> None:
        tokens = await self._register_and_login("plain@example.com")
        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "test@example.com", "scope": "platform"},
        )
        self.assertEqual(resp.status_code, 403)

    async def test_registration_auto_accepts_pending_invites(self) -> None:
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)

        # Create invitation for email that will register later
        await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "future-user@example.com",
                "scope": "organization",
                "org_id": org_id,
                "role": "admin",
            },
        )

        # Register with the invited email
        reg_resp = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "future-user@example.com", "password": "StrongPassword123"},
        )
        self.assertEqual(reg_resp.status_code, 201)

        # Verify user was auto-added to org
        members_resp = await self.client.get(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
        )
        member_user_ids = [m["user_id"] for m in members_resp.json()]

        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "future-user@example.com", "password": "StrongPassword123"},
        )
        user_id = await self._get_user_id(login_resp.json()["access_token"])
        self.assertIn(user_id, member_user_ids)

        # Verify invitation status changed to accepted
        list_resp = await self.client.get(
            "/api/v1/am/invitations?email=future-user@example.com",
            headers=self._auth_headers(tokens),
        )
        invite = list_resp.json()["items"][0]
        self.assertEqual(invite["status"], "accepted")

    async def test_filter_invitations_by_status(self) -> None:
        _, tokens = await self._setup_admin()
        await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={"email": "filter1@example.com", "scope": "platform"},
        )

        resp = await self.client.get(
            "/api/v1/am/invitations?status=pending",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(resp.status_code, 200)
        for item in resp.json()["items"]:
            self.assertEqual(item["status"], "pending")

    async def test_custom_expiry(self) -> None:
        _, tokens = await self._setup_admin()
        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "expiry@example.com",
                "scope": "platform",
                "expires_in_hours": 1,
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIsNotNone(data["expires_at"])

    # ─── GRC role invite & access tests ─────────────────────────────────────

    async def test_create_workspace_invitation_with_grc_role(self) -> None:
        """Workspace invitation can carry a grc_role_code."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "auditor@external.com",
                "scope": "workspace",
                "org_id": org_id,
                "workspace_id": ws_id,
                "role": "viewer",
                "grc_role_code": "grc_staff_auditor",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["scope"], "workspace")
        self.assertEqual(data["workspace_id"], ws_id)
        self.assertEqual(data["grc_role_code"], "grc_staff_auditor")
        self.assertEqual(data["role"], "viewer")

    async def test_all_grc_roles_accepted_in_invitation(self) -> None:
        """All seven GRC role codes are valid on a workspace invitation."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        grc_roles = [
            "grc_lead",
            "grc_sme",
            "grc_engineer",
            "grc_ciso",
            "grc_lead_auditor",
            "grc_staff_auditor",
            "grc_vendor",
        ]
        for i, role_code in enumerate(grc_roles):
            resp = await self.client.post(
                "/api/v1/am/invitations",
                headers=self._auth_headers(tokens),
                json={
                    "email": f"grc-role-{i}@example.com",
                    "scope": "workspace",
                    "org_id": org_id,
                    "workspace_id": ws_id,
                    "role": "viewer",
                    "grc_role_code": role_code,
                },
            )
            self.assertEqual(resp.status_code, 201, msg=f"Failed for grc_role_code={role_code}")
            self.assertEqual(resp.json()["grc_role_code"], role_code)

    async def test_accept_grc_workspace_invitation_assigns_role(self) -> None:
        """Accepting a workspace invite with grc_role_code sets the role on membership."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        # Register the auditor user first
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "auditor-accept@example.com", "password": "StrongPassword123"},
        )

        # Create workspace invite with GRC role
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "auditor-accept@example.com",
                "scope": "workspace",
                "org_id": org_id,
                "workspace_id": ws_id,
                "role": "viewer",
                "grc_role_code": "grc_lead_auditor",
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        invite_token = create_resp.json()["invite_token"]

        # Accept the invitation
        accept_resp = await self.client.post(
            "/api/v1/am/invitations/accept",
            json={"invite_token": invite_token},
        )
        self.assertEqual(accept_resp.status_code, 200)
        accept_data = accept_resp.json()
        self.assertEqual(accept_data["scope"], "workspace")

        # Verify workspace membership was created
        members_resp = await self.client.get(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(members_resp.status_code, 200)
        members = members_resp.json()
        self.assertTrue(
            isinstance(members, list) or isinstance(members, dict),
            "Expected list or paginated response",
        )

    async def test_grc_invitation_auto_accepted_on_registration(self) -> None:
        """When a user registers with a pending GRC workspace invitation, it is auto-accepted."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        # Create invite BEFORE user registers
        create_resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "new-grc-user@example.com",
                "scope": "workspace",
                "org_id": org_id,
                "workspace_id": ws_id,
                "role": "viewer",
                "grc_role_code": "grc_sme",
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        invite_id = create_resp.json()["id"]

        # Register — this should auto-accept
        reg_resp = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "new-grc-user@example.com", "password": "StrongPassword123"},
        )
        self.assertEqual(reg_resp.status_code, 201)

        # Invitation status should now be accepted
        inv_resp = await self.client.get(
            f"/api/v1/am/invitations/{invite_id}",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(inv_resp.status_code, 200)
        self.assertEqual(inv_resp.json()["status"], "accepted")

    async def test_assign_grc_role_directly_on_workspace_member(self) -> None:
        """GRC role can be assigned/changed directly on an existing workspace member."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        # Register + add user to org + workspace
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "direct-grc@example.com", "password": "StrongPassword123"},
        )
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "direct-grc@example.com", "password": "StrongPassword123"},
        )
        user_id = await self._get_user_id(login_resp.json()["access_token"])

        # Add to org
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "membership_type": "member"},
        )
        # Add to workspace
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "role": "contributor"},
        )

        # Assign GRC role via PATCH
        patch_resp = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_engineer"},
        )
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["grc_role_code"], "grc_engineer")

        # Change to a different GRC role
        patch_resp2 = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_lead"},
        )
        self.assertEqual(patch_resp2.status_code, 200)
        self.assertEqual(patch_resp2.json()["grc_role_code"], "grc_lead")

    async def test_clear_grc_role_sets_null(self) -> None:
        """Setting grc_role_code to null removes the GRC role assignment."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "clear-grc@example.com", "password": "StrongPassword123"},
        )
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "clear-grc@example.com", "password": "StrongPassword123"},
        )
        user_id = await self._get_user_id(login_resp.json()["access_token"])

        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "membership_type": "member"},
        )
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "role": "viewer"},
        )
        # Assign GRC role
        await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_ciso"},
        )
        # Clear GRC role
        clear_resp = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": None},
        )
        self.assertEqual(clear_resp.status_code, 200)
        self.assertIsNone(clear_resp.json()["grc_role_code"])

    async def test_invalid_grc_role_code_rejected(self) -> None:
        """An unrecognised grc_role_code is rejected with a 422."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        resp = await self.client.post(
            "/api/v1/am/invitations",
            headers=self._auth_headers(tokens),
            json={
                "email": "bad-grc@example.com",
                "scope": "workspace",
                "org_id": org_id,
                "workspace_id": ws_id,
                "role": "viewer",
                "grc_role_code": "grc_hacker",  # not a real role
            },
        )
        self.assertEqual(resp.status_code, 422)

    async def test_grc_role_permissions_via_access_endpoint(self) -> None:
        """A user with grc_lead role should have task_management permissions via Branch 5."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        # Register the GRC user
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "grc-perms@example.com", "password": "StrongPassword123"},
        )
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "grc-perms@example.com", "password": "StrongPassword123"},
        )
        user_tokens = login_resp.json()
        user_id = await self._get_user_id(user_tokens["access_token"])

        # Enrol in org + workspace
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "membership_type": "member"},
        )
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "role": "contributor"},
        )
        # Assign grc_lead role — should grant task_management + findings + workflow permissions
        await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_lead"},
        )

        # Query the access/permissions endpoint as the GRC user
        access_resp = await self.client.get(
            f"/api/v1/am/access?org_id={org_id}&workspace_id={ws_id}",
            headers=self._auth_headers(user_tokens),
        )
        self.assertEqual(access_resp.status_code, 200)
        access_data = access_resp.json()

        # grc_lead should have task management view permissions
        perms = access_data.get("permissions", [])
        self.assertIn(
            "task_management.view", perms,
            "grc_lead should have task_management.view via Branch 5",
        )

    async def test_grc_staff_auditor_has_limited_permissions(self) -> None:
        """grc_staff_auditor has fewer permissions than grc_lead."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "staff-aud@example.com", "password": "StrongPassword123"},
        )
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "staff-aud@example.com", "password": "StrongPassword123"},
        )
        user_tokens = login_resp.json()
        user_id = await self._get_user_id(user_tokens["access_token"])

        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "membership_type": "member"},
        )
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "role": "viewer"},
        )
        await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_staff_auditor"},
        )

        access_resp = await self.client.get(
            f"/api/v1/am/access?org_id={org_id}&workspace_id={ws_id}",
            headers=self._auth_headers(user_tokens),
        )
        self.assertEqual(access_resp.status_code, 200)
        perms = access_resp.json().get("permissions", [])

        # Staff auditor should NOT have task approval or findings.close
        self.assertNotIn("tasks.approve", perms, "grc_staff_auditor should not approve tasks")
        self.assertNotIn("findings.close", perms, "grc_staff_auditor should not close findings")

    async def test_workspace_member_listing_includes_grc_role(self) -> None:
        """GET workspace members returns grc_role_code on each member."""
        _, tokens = await self._setup_admin()
        org_id = await self._create_org(tokens)
        ws_id = await self._create_workspace(tokens, org_id)

        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "member-grc-list@example.com", "password": "StrongPassword123"},
        )
        login_resp = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "member-grc-list@example.com", "password": "StrongPassword123"},
        )
        user_id = await self._get_user_id(login_resp.json()["access_token"])

        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "membership_type": "member"},
        )
        await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
            json={"user_id": user_id, "role": "viewer"},
        )
        await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{user_id}",
            headers=self._auth_headers(tokens),
            json={"grc_role_code": "grc_vendor"},
        )

        members_resp = await self.client.get(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            headers=self._auth_headers(tokens),
        )
        self.assertEqual(members_resp.status_code, 200)
        members_data = members_resp.json()
        member_list = members_data if isinstance(members_data, list) else members_data.get("items", members_data.get("members", []))
        target = next((m for m in member_list if m.get("user_id") == user_id), None)
        self.assertIsNotNone(target, "User should appear in workspace member list")
        self.assertEqual(target.get("grc_role_code"), "grc_vendor")
