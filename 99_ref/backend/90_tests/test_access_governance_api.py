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
        self._temp_dir = tempfile.TemporaryDirectory(prefix="kcontrol-pg-gov-")
        self.base_path = Path(self._temp_dir.name)
        self.data_path = self.base_path / "data"
        self.port = self._find_free_port()
        self.database_name = "kcontrol_gov_test"
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

    def cleanup_best_effort(self) -> None:
        try:
            shutil.rmtree(self.base_path, ignore_errors=True)
        finally:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass

    @staticmethod
    def _find_free_port() -> int:
        with socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


def _make_settings(database_dsn: str) -> Settings:
    return Settings(
        environment="test",
        app_name="kcontrol-gov-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=True,
        database_url=database_dsn,
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-gov-secret",
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


class AccessGovernanceApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = _PostgresTestServer()
        try:
            cls.postgres.start()
        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as exc:
            cls.postgres.cleanup_best_effort()
            raise unittest.SkipTest(f"Local Postgres test server is unavailable in this environment: {exc}") from exc

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
        self._auditor_workspace_migrations_applied = False

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
        """Directly insert user into the seeded platform_super_admin group."""
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
        finally:
            await conn.close()

    async def _get_user_id(self, access_token: str) -> str:
        resp = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return resp.json()["user_id"]

    async def _apply_sql_file(self, relative_path: str) -> None:
        sql_path = Path(relative_path)
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            await conn.execute(sql_path.read_text(encoding="utf-8"))
        finally:
            await conn.close()

    async def _apply_auditor_workspace_migrations(self) -> None:
        if self._auditor_workspace_migrations_applied:
            return
        for relative_path in (
            "backend/01_sql_migrations/01_migrated/20260402_add-engagement-memberships-foundation.sql",
            "backend/01_sql_migrations/01_migrated/20260402_add-auditor-evidence-request-guardrails.sql",
            "backend/01_sql_migrations/01_migrated/20260402_add-auditor-task-finding-flags.sql",
            "backend/01_sql_migrations/01_migrated/20260402_map-auditor-workspace-role-permissions.sql",
            "backend/01_sql_migrations/01_migrated/20260407_enable-auditor-workspace-prod-flags.sql",
        ):
            await self._apply_sql_file(relative_path)
        self._auditor_workspace_migrations_applied = True

    # ─── access context ──────────────────────────────────────────────────────

    async def test_access_context_returns_empty_for_unprivileged_user(self) -> None:
        tokens = await self._register_and_login("plain@example.com")
        resp = await self.client.get(
            "/api/v1/am/access",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("platform", data)
        self.assertEqual(data["platform"]["actions"], [])
        self.assertIsNone(data["current_org"])
        self.assertIsNone(data["current_workspace"])

    async def test_access_context_returns_actions_for_super_admin(self) -> None:
        tokens = await self._register_and_login("sadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            "/api/v1/am/access",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        platform_actions = data["platform"]["actions"]
        self.assertGreater(len(platform_actions), 0)
        codes = {a["action_code"] for a in platform_actions}
        self.assertIn("view", codes)
        self.assertIn("enable", codes)

    async def test_access_context_includes_auditor_workspace_actions_for_super_admin(self) -> None:
        await self._apply_auditor_workspace_migrations()
        tokens = await self._register_and_login("auditorflags@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            "/api/v1/am/access",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)

        actions = {
            (action["feature_code"], action["action_code"])
            for action in resp.json()["platform"]["actions"]
        }
        self.assertIn(("audit_workspace_auditor_portfolio", "view"), actions)
        self.assertIn(("audit_workspace_engagement_membership", "view"), actions)
        self.assertIn(("audit_workspace_control_access", "view"), actions)
        self.assertIn(("audit_workspace_evidence_requests", "approve"), actions)
        self.assertIn(("audit_workspace_auditor_findings", "create"), actions)
        self.assertIn(("audit_workspace_auditor_tasks", "update"), actions)

    async def test_access_context_requires_auth(self) -> None:
        resp = await self.client.get("/api/v1/am/access")
        self.assertEqual(resp.status_code, 401)

    # ─── feature flags ───────────────────────────────────────────────────────

    async def test_list_feature_flags_requires_permission(self) -> None:
        tokens = await self._register_and_login("noperm@example.com")
        resp = await self.client.get(
            "/api/v1/am/features",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 403)

    async def test_list_feature_flags_as_super_admin(self) -> None:
        tokens = await self._register_and_login("ffadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            "/api/v1/am/features",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("flags", data)
        self.assertIn("categories", data)
        codes = [f["code"] for f in data["flags"]]
        self.assertIn("auth_password_login", codes)
        self.assertIn("feature_flag_registry", codes)

    async def test_create_and_update_feature_flag(self) -> None:
        tokens = await self._register_and_login("ffcreate@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = await self.client.post(
            "/api/v1/am/features",
            json={
                "code": "test_new_flag",
                "name": "Test New Flag",
                "description": "A test flag for integration tests.",
                "category_code": "admin",
                "access_mode": "permissioned",
                "lifecycle_state": "planned",
                "initial_audience": "platform_super_admin",
                "env_dev": True,
            },
            headers=auth,
        )
        self.assertEqual(create_resp.status_code, 201)
        flag = create_resp.json()
        self.assertEqual(flag["code"], "test_new_flag")
        self.assertTrue(flag["env_dev"])
        self.assertFalse(flag["env_staging"])

        patch_resp = await self.client.patch(
            f"/api/v1/am/features/test_new_flag",
            json={"lifecycle_state": "active", "env_staging": True},
            headers=auth,
        )
        self.assertEqual(patch_resp.status_code, 200)
        updated = patch_resp.json()
        self.assertEqual(updated["lifecycle_state"], "active")
        self.assertTrue(updated["env_staging"])

    async def test_create_duplicate_feature_flag_returns_409(self) -> None:
        tokens = await self._register_and_login("ffdup@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {
            "code": "dup_flag", "name": "Dup", "description": "dup",
            "category_code": "admin", "access_mode": "permissioned",
        }
        await self.client.post("/api/v1/am/features", json=payload, headers=auth)
        resp = await self.client.post("/api/v1/am/features", json=payload, headers=auth)
        self.assertEqual(resp.status_code, 409)

    async def test_update_nonexistent_flag_returns_404(self) -> None:
        tokens = await self._register_and_login("ffnotfound@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.patch(
            "/api/v1/am/features/does_not_exist",
            json={"lifecycle_state": "active"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 404)

    async def test_super_admin_can_disable_auditor_capabilities_independently(self) -> None:
        await self._apply_auditor_workspace_migrations()
        tokens = await self._register_and_login("auditor-toggle@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}
        dummy_engagement_id = str(uuid4())

        flag_checks = (
            ("audit_workspace_auditor_portfolio", "GET", "/api/v1/engagements/my-engagements"),
            ("audit_workspace_control_access", "GET", f"/api/v1/engagements/{dummy_engagement_id}/controls"),
            ("audit_workspace_evidence_requests", "GET", f"/api/v1/engagements/{dummy_engagement_id}/requests"),
            ("audit_workspace_auditor_tasks", "GET", f"/api/v1/engagements/{dummy_engagement_id}/tasks"),
            ("audit_workspace_auditor_findings", "GET", f"/api/v1/engagements/{dummy_engagement_id}/assessments"),
        )

        for flag_code, method, path in flag_checks:
            disabled = await self.client.patch(
                f"/api/v1/am/features/{flag_code}",
                json={"env_dev": False},
                headers=auth,
            )
            self.assertEqual(disabled.status_code, 200, f"Expected {flag_code} to disable cleanly")

            blocked = await self.client.request(method, path, headers=auth)
            self.assertEqual(
                blocked.status_code,
                503,
                f"Expected {flag_code} to block its guarded route when disabled",
            )

            enabled = await self.client.patch(
                f"/api/v1/am/features/{flag_code}",
                json={"env_dev": True},
                headers=auth,
            )
            self.assertEqual(enabled.status_code, 200, f"Expected {flag_code} to re-enable cleanly")

            unblocked = await self.client.request(method, path, headers=auth)
            self.assertNotEqual(
                unblocked.status_code,
                503,
                f"Expected {flag_code} to stop returning feature-disabled after re-enable",
            )

    async def test_auditor_workspace_flags_are_enabled_for_prod_after_rollout_migration(self) -> None:
        await self._apply_auditor_workspace_migrations()
        conn = await asyncpg.connect(self.postgres.database_dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT code, env_prod
                FROM "03_auth_manage"."14_dim_feature_flags"
                WHERE code = ANY($1::text[])
                ORDER BY code
                """,
                [
                    "audit_workspace_auditor_portfolio",
                    "audit_workspace_engagement_membership",
                    "audit_workspace_control_access",
                    "audit_workspace_evidence_requests",
                    "audit_workspace_auditor_tasks",
                    "audit_workspace_auditor_findings",
                ],
            )
        finally:
            await conn.close()

        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertTrue(row["env_prod"], f"Expected {row['code']} to be enabled for prod")

    # ─── roles ──────────────────────────────────────────────────────────────

    async def test_list_roles_as_super_admin(self) -> None:
        tokens = await self._register_and_login("roleview@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            "/api/v1/am/roles",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("roles", data)
        self.assertIn("levels", data)
        codes = [r["code"] for r in data["roles"]]
        self.assertIn("platform_super_admin", codes)

    async def test_create_role_and_assign_revoke_permission(self) -> None:
        tokens = await self._register_and_login("rolecreate@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = await self.client.post(
            "/api/v1/am/roles",
            json={
                "code": "test_org_admin",
                "name": "Test Org Admin",
                "description": "A test org admin role.",
                "role_level_code": "org",
            },
            headers=auth,
        )
        self.assertEqual(create_resp.status_code, 201)
        role = create_resp.json()
        role_id = role["id"]
        self.assertEqual(role["code"], "test_org_admin")
        self.assertEqual(len(role["permissions"]), 0)

        # assign a permission (use a known seeded permission id)
        # First fetch the permission ID from feature list
        flags_resp = await self.client.get("/api/v1/am/features", headers=auth)
        flags_data = flags_resp.json()
        perm_id = None
        for flag in flags_data["flags"]:
            for perm in flag["permissions"]:
                if perm["code"] == "feature_flag_registry.view":
                    perm_id = perm["id"]
                    break
            if perm_id:
                break
        self.assertIsNotNone(perm_id)

        assign_resp = await self.client.post(
            f"/api/v1/am/roles/{role_id}/permissions",
            json={"feature_permission_id": perm_id},
            headers=auth,
        )
        self.assertEqual(assign_resp.status_code, 201)
        role_with_perm = assign_resp.json()
        self.assertEqual(len(role_with_perm["permissions"]), 1)
        self.assertEqual(role_with_perm["permissions"][0]["feature_permission_code"], "feature_flag_registry.view")

        # duplicate assign returns 409
        dup_resp = await self.client.post(
            f"/api/v1/am/roles/{role_id}/permissions",
            json={"feature_permission_id": perm_id},
            headers=auth,
        )
        self.assertEqual(dup_resp.status_code, 409)

        # revoke
        revoke_resp = await self.client.delete(
            f"/api/v1/am/roles/{role_id}/permissions/{perm_id}",
            headers=auth,
        )
        self.assertEqual(revoke_resp.status_code, 204)

    async def test_create_duplicate_role_returns_409(self) -> None:
        tokens = await self._register_and_login("roledup@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {"code": "dup_role", "name": "Dup", "description": "dup", "role_level_code": "org"}
        await self.client.post("/api/v1/am/roles", json=payload, headers=auth)
        resp = await self.client.post("/api/v1/am/roles", json=payload, headers=auth)
        self.assertEqual(resp.status_code, 409)

    # ─── groups ─────────────────────────────────────────────────────────────

    async def test_list_groups_as_super_admin(self) -> None:
        tokens = await self._register_and_login("grpview@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            "/api/v1/am/groups",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        codes = [g["code"] for g in data["groups"]]
        self.assertIn("platform_super_admin", codes)

    async def test_create_group_and_manage_members_and_roles(self) -> None:
        tokens = await self._register_and_login("grpcreate@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        # create group
        grp_resp = await self.client.post(
            "/api/v1/am/groups",
            json={"code": "test_group", "name": "Test Group",
                  "description": "Integration test group.", "role_level_code": "org"},
            headers=auth,
        )
        self.assertEqual(grp_resp.status_code, 201)
        group = grp_resp.json()
        group_id = group["id"]
        self.assertEqual(group["code"], "test_group")
        self.assertEqual(group["members"], [])

        # register a second user to add as member
        tokens2 = await self._register_and_login("member@example.com")
        member_id = await self._get_user_id(tokens2["access_token"])

        # add member
        add_resp = await self.client.post(
            f"/api/v1/am/groups/{group_id}/members",
            json={"user_id": member_id},
            headers=auth,
        )
        self.assertEqual(add_resp.status_code, 201)
        grp_after_add = add_resp.json()
        member_ids = [m["user_id"] for m in grp_after_add["members"]]
        self.assertIn(member_id, member_ids)

        # duplicate member returns 409
        dup_resp = await self.client.post(
            f"/api/v1/am/groups/{group_id}/members",
            json={"user_id": member_id},
            headers=auth,
        )
        self.assertEqual(dup_resp.status_code, 409)

        # create a role to assign to group
        role_resp = await self.client.post(
            "/api/v1/am/roles",
            json={"code": "grp_test_role", "name": "Group Test Role",
                  "description": "For group test.", "role_level_code": "org"},
            headers=auth,
        )
        role_id = role_resp.json()["id"]

        # assign role to group
        assign_resp = await self.client.post(
            f"/api/v1/am/groups/{group_id}/roles",
            json={"role_id": role_id},
            headers=auth,
        )
        self.assertEqual(assign_resp.status_code, 201)
        grp_with_role = assign_resp.json()
        role_ids = [r["role_id"] for r in grp_with_role["roles"]]
        self.assertIn(role_id, role_ids)

        # revoke role
        revoke_resp = await self.client.delete(
            f"/api/v1/am/groups/{group_id}/roles/{role_id}",
            headers=auth,
        )
        self.assertEqual(revoke_resp.status_code, 204)

        # remove member
        remove_resp = await self.client.delete(
            f"/api/v1/am/groups/{group_id}/members/{member_id}",
            headers=auth,
        )
        self.assertEqual(remove_resp.status_code, 204)

    async def test_group_access_denied_without_permission(self) -> None:
        tokens = await self._register_and_login("grpnoperm@example.com")
        resp = await self.client.get(
            "/api/v1/am/groups",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 403)

    # ─── end-to-end flow ────────────────────────────────────────────────────

    async def test_full_governance_pipeline(self) -> None:
        """
        Full pipeline: super admin creates a role, assigns a permission,
        creates a group, assigns the role to the group, adds a user to the
        group, then that user can resolve the granted action from /access.
        """
        # setup super admin
        admin_tokens = await self._register_and_login("goveadmin@example.com")
        admin_id = await self._get_user_id(admin_tokens["access_token"])
        await self._grant_super_admin(admin_id)
        auth = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        # get a known permission id (feature_flag_registry.view)
        flags_resp = await self.client.get("/api/v1/am/features", headers=auth)
        perm_id = None
        for flag in flags_resp.json()["flags"]:
            for perm in flag["permissions"]:
                if perm["code"] == "feature_flag_registry.view":
                    perm_id = perm["id"]
                    break
            if perm_id:
                break
        self.assertIsNotNone(perm_id)

        # create role
        role_resp = await self.client.post(
            "/api/v1/am/roles",
            json={"code": "pipeline_viewer", "name": "Pipeline Viewer",
                  "description": "Can view feature flags.", "role_level_code": "super_admin"},
            headers=auth,
        )
        self.assertEqual(role_resp.status_code, 201)
        role_id = role_resp.json()["id"]

        # assign permission to role
        await self.client.post(
            f"/api/v1/am/roles/{role_id}/permissions",
            json={"feature_permission_id": perm_id},
            headers=auth,
        )

        # create group
        grp_resp = await self.client.post(
            "/api/v1/am/groups",
            json={"code": "pipeline_viewers", "name": "Pipeline Viewers",
                  "description": "Viewers group.", "role_level_code": "super_admin"},
            headers=auth,
        )
        self.assertEqual(grp_resp.status_code, 201)
        group_id = grp_resp.json()["id"]

        # assign role to group
        await self.client.post(
            f"/api/v1/am/groups/{group_id}/roles",
            json={"role_id": role_id},
            headers=auth,
        )

        # register regular user
        user_tokens = await self._register_and_login("govuser@example.com")
        user_id = await self._get_user_id(user_tokens["access_token"])

        # add user to group
        await self.client.post(
            f"/api/v1/am/groups/{group_id}/members",
            json={"user_id": user_id},
            headers=auth,
        )

        # user's access context should now include feature_flag_registry.view
        access_resp = await self.client.get(
            "/api/v1/am/access",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
        )
        self.assertEqual(access_resp.status_code, 200)
        actions = access_resp.json()["platform"]["actions"]
        action_keys = {(a["feature_code"], a["action_code"]) for a in actions}
        self.assertIn(("feature_flag_registry", "view"), action_keys)

        # user can now call GET /features
        features_resp = await self.client.get(
            "/api/v1/am/features",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
        )
        self.assertEqual(features_resp.status_code, 200)


    # ─── org types ───────────────────────────────────────────────────────────

    async def test_list_org_types_is_public(self) -> None:
        resp = await self.client.get("/api/v1/am/org-types")
        self.assertEqual(resp.status_code, 200)
        codes = [t["code"] for t in resp.json()]
        self.assertIn("company", codes)
        self.assertIn("personal", codes)

    # ─── orgs ────────────────────────────────────────────────────────────────

    async def test_create_and_update_org(self) -> None:
        tokens = await self._register_and_login("orgadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        # list (empty)
        list_resp = await self.client.get("/api/v1/am/orgs", headers=auth)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["total"], 0)

        # create
        create_resp = await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "Acme Corp", "slug": "acme-corp", "org_type_code": "company"},
            headers=auth,
        )
        self.assertEqual(create_resp.status_code, 201)
        org = create_resp.json()
        self.assertEqual(org["slug"], "acme-corp")
        self.assertEqual(org["org_type_code"], "company")
        self.assertTrue(org["is_active"])
        org_id = org["id"]

        # list now has 1
        list_resp2 = await self.client.get("/api/v1/am/orgs", headers=auth)
        self.assertEqual(list_resp2.json()["total"], 1)

        # update
        patch_resp = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}",
            json={"name": "Acme Corporation"},
            headers=auth,
        )
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["name"], "Acme Corporation")

        # disable
        disable_resp = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}",
            json={"is_disabled": True},
            headers=auth,
        )
        self.assertEqual(disable_resp.status_code, 200)
        self.assertFalse(disable_resp.json()["is_active"])

    async def test_duplicate_org_slug_returns_409(self) -> None:
        tokens = await self._register_and_login("orgdup@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {"name": "Dup Org", "slug": "dup-org-slug", "org_type_code": "company"}
        await self.client.post("/api/v1/am/orgs", json=payload, headers=auth)
        resp = await self.client.post("/api/v1/am/orgs", json=payload, headers=auth)
        self.assertEqual(resp.status_code, 409)

    async def test_org_member_management(self) -> None:
        tokens = await self._register_and_login("orgmemadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        # create org
        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "Org Members Test", "slug": "org-members-test", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        # register another user
        tokens2 = await self._register_and_login("orgmember@example.com")
        member_id = await self._get_user_id(tokens2["access_token"])

        # list empty
        members = (await self.client.get(f"/api/v1/am/orgs/{org_id}/members", headers=auth)).json()
        self.assertEqual(members, [])

        # add member
        add_resp = await self.client.post(
            f"/api/v1/am/orgs/{org_id}/members",
            json={"user_id": member_id, "role": "admin"},
            headers=auth,
        )
        self.assertEqual(add_resp.status_code, 201)
        self.assertEqual(add_resp.json()["role"], "admin")

        members_after = (await self.client.get(f"/api/v1/am/orgs/{org_id}/members", headers=auth)).json()
        self.assertEqual(len(members_after), 1)

        # remove member
        remove_resp = await self.client.delete(
            f"/api/v1/am/orgs/{org_id}/members/{member_id}",
            headers=auth,
        )
        self.assertEqual(remove_resp.status_code, 204)

    async def test_org_requires_permission(self) -> None:
        tokens = await self._register_and_login("orgnoperm@example.com")
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await self.client.get("/api/v1/am/orgs", headers=auth)
        self.assertEqual(resp.status_code, 403)

    # ─── workspace types ─────────────────────────────────────────────────────

    async def test_list_workspace_types_is_public(self) -> None:
        resp = await self.client.get("/api/v1/am/workspace-types")
        self.assertEqual(resp.status_code, 200)
        codes = [t["code"] for t in resp.json()]
        self.assertIn("project", codes)

    # ─── workspaces ──────────────────────────────────────────────────────────

    async def test_create_and_update_workspace(self) -> None:
        tokens = await self._register_and_login("wsadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        # need an org first
        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "Workspace Org", "slug": "workspace-org", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        # list workspaces (empty)
        list_resp = await self.client.get(f"/api/v1/am/orgs/{org_id}/workspaces", headers=auth)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["total"], 0)

        # create workspace
        create_resp = await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces",
            json={"name": "Dev Workspace", "slug": "dev-workspace", "workspace_type_code": "project"},
            headers=auth,
        )
        self.assertEqual(create_resp.status_code, 201)
        ws = create_resp.json()
        self.assertEqual(ws["slug"], "dev-workspace")
        self.assertEqual(ws["org_id"], org_id)
        self.assertIsNone(ws["product_id"])
        ws_id = ws["id"]

        # list has 1
        list_resp2 = await self.client.get(f"/api/v1/am/orgs/{org_id}/workspaces", headers=auth)
        self.assertEqual(list_resp2.json()["total"], 1)

        # update name
        patch_resp = await self.client.patch(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}",
            json={"name": "Development Workspace"},
            headers=auth,
        )
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["name"], "Development Workspace")

    async def test_duplicate_workspace_slug_returns_409(self) -> None:
        tokens = await self._register_and_login("wsdup@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "WS Dup Org", "slug": "ws-dup-org", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        payload = {"name": "Dup WS", "slug": "dup-ws-slug", "workspace_type_code": "project"}
        await self.client.post(f"/api/v1/am/orgs/{org_id}/workspaces", json=payload, headers=auth)
        resp = await self.client.post(f"/api/v1/am/orgs/{org_id}/workspaces", json=payload, headers=auth)
        self.assertEqual(resp.status_code, 409)

    async def test_invalid_workspace_type_returns_422(self) -> None:
        tokens = await self._register_and_login("wsbadtype@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "WS Bad Type Org", "slug": "ws-bad-type-org", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        resp = await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces",
            json={"name": "Bad Type WS", "slug": "bad-type-ws", "workspace_type_code": "security"},
            headers=auth,
        )
        self.assertEqual(resp.status_code, 422)
        body = resp.json()
        self.assertEqual(body["error"]["code"], "validation_error")
        self.assertIn("workspace_type_code", body["error"]["message"])

    async def test_workspace_member_management(self) -> None:
        tokens = await self._register_and_login("wsmemadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "WS Mem Org", "slug": "ws-mem-org", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        ws = (await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces",
            json={"name": "WS Mem WS", "slug": "ws-mem-ws", "workspace_type_code": "project"},
            headers=auth,
        )).json()
        ws_id = ws["id"]

        tokens2 = await self._register_and_login("wsmember@example.com")
        member_id = await self._get_user_id(tokens2["access_token"])

        add_resp = await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members",
            json={"user_id": member_id, "role": "viewer"},
            headers=auth,
        )
        self.assertEqual(add_resp.status_code, 201)
        self.assertEqual(add_resp.json()["role"], "viewer")

        members = (await self.client.get(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members", headers=auth
        )).json()
        self.assertEqual(len(members), 1)

        remove_resp = await self.client.delete(
            f"/api/v1/am/orgs/{org_id}/workspaces/{ws_id}/members/{member_id}",
            headers=auth,
        )
        self.assertEqual(remove_resp.status_code, 204)

    # ─── nested access context ────────────────────────────────────────────────

    async def test_nested_access_context_with_org_and_workspace(self) -> None:
        """
        Verify that GET /access?org_id=X&workspace_id=Y returns a 3-level
        nested response with platform, current_org, and current_workspace.
        """
        tokens = await self._register_and_login("nestadmin@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        # create org + workspace
        org = (await self.client.post(
            "/api/v1/am/orgs",
            json={"name": "Nest Org", "slug": "nest-org", "org_type_code": "company"},
            headers=auth,
        )).json()
        org_id = org["id"]

        ws = (await self.client.post(
            f"/api/v1/am/orgs/{org_id}/workspaces",
            json={"name": "Nest WS", "slug": "nest-ws", "workspace_type_code": "project"},
            headers=auth,
        )).json()
        ws_id = ws["id"]

        # platform only
        resp_platform = await self.client.get("/api/v1/am/access", headers=auth)
        self.assertEqual(resp_platform.status_code, 200)
        data_platform = resp_platform.json()
        self.assertIsNotNone(data_platform["platform"])
        self.assertIsNone(data_platform["current_org"])
        self.assertIsNone(data_platform["current_workspace"])

        # with org context
        resp_org = await self.client.get(
            f"/api/v1/am/access?org_id={org_id}", headers=auth
        )
        self.assertEqual(resp_org.status_code, 200)
        data_org = resp_org.json()
        self.assertIsNotNone(data_org["current_org"])
        self.assertEqual(data_org["current_org"]["org_id"], org_id)
        self.assertEqual(data_org["current_org"]["slug"], "nest-org")
        self.assertIsNone(data_org["current_workspace"])

        # with org + workspace context
        resp_ws = await self.client.get(
            f"/api/v1/am/access?org_id={org_id}&workspace_id={ws_id}", headers=auth
        )
        self.assertEqual(resp_ws.status_code, 200)
        data_ws = resp_ws.json()
        self.assertIsNotNone(data_ws["current_org"])
        self.assertIsNotNone(data_ws["current_workspace"])
        self.assertEqual(data_ws["current_workspace"]["workspace_id"], ws_id)
        self.assertEqual(data_ws["current_workspace"]["slug"], "nest-ws")
        self.assertEqual(data_ws["current_workspace"]["org_id"], org_id)
        self.assertIsNone(data_ws["current_workspace"]["product_id"])

    async def test_access_context_with_unknown_org_returns_none_for_org(self) -> None:
        tokens = await self._register_and_login("nestunknown@example.com")
        user_id = await self._get_user_id(tokens["access_token"])
        await self._grant_super_admin(user_id)

        resp = await self.client.get(
            f"/api/v1/am/access?org_id={uuid4()}",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # unknown org → current_org is None (org info not found)
        self.assertIsNone(data["current_org"])


if __name__ == "__main__":
    unittest.main()
