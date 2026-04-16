from __future__ import annotations

from importlib import import_module
from pathlib import Path
from socket import socket
import shutil
import subprocess
import tempfile
import unittest

import asyncpg
import httpx


application_module = import_module("backend.01_core.application")
settings_module = import_module("backend.00_config.settings")

create_app = application_module.create_app
Settings = settings_module.Settings


class _PostgresTestServer:
    def __init__(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory(prefix="kcontrol-pl-")
        self.base_path = Path(self._temp_dir.name)
        self.data_path = self.base_path / "data"
        self.port = self._find_free_port()
        self.database_name = "kcontrol_passwordless_test"
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
            self._temp_dir.cleanup()

    @staticmethod
    def _find_free_port() -> int:
        with socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


def _base_settings(dsn: str, **overrides) -> Settings:
    base: dict = dict(
        environment="test",
        app_name="kcontrol-passwordless-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=True,
        database_url=dsn,
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-secret",
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
        migration_directory=Path("backend/90_tests/test_migrations"),
        otel_enabled=False,
        otel_traces_enabled=False,
        otel_function_trace_enabled=False,
        magic_link_enabled=True,
        magic_link_default_ttl_hours=24,
        magic_link_frontend_verify_url="http://localhost:3000/magic-link/verify",
    )
    base.update(overrides)
    return Settings(**base)


class PasswordlessAuthIntegrationTests(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = _PostgresTestServer()
        cls.postgres.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.postgres.stop()

    async def asyncSetUp(self) -> None:
        await self._reset_schema()
        self.settings = _base_settings(self.postgres.database_dsn)
        self.app = create_app(self.settings)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _reset_schema(self) -> None:
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            await conn.execute('DROP SCHEMA IF EXISTS "03_auth_manage" CASCADE')
            await conn.execute('DROP SCHEMA IF EXISTS "03_notifications" CASCADE')
            await conn.execute('DROP SCHEMA IF EXISTS "01_dev_features" CASCADE')
        finally:
            await conn.close()

    async def _fetch_audit_events(self) -> list[str]:
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            rows = await conn.fetch('SELECT event_type FROM "03_auth_manage"."40_aud_events" ORDER BY occurred_at ASC')
            return [r["event_type"] for r in rows]
        finally:
            await conn.close()

    async def _request_magic_link(self, email: str) -> httpx.Response:
        return await self.client.post(
            "/api/v1/auth/passwordless/request",
            json={"email": email},
        )

    async def _verify_magic_link(self, token: str) -> httpx.Response:
        return await self.client.post(
            f"/api/v1/auth/passwordless/verify?token={token}",
        )

    async def _register_full_user(self, email: str, password: str = "StrongPassword123", username: str | None = None) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": email, "password": password, "username": username or email.split("@")[0]},
        )

    # ── test 1: request for non-existent email succeeds silently ─────────────

    async def test_request_returns_success_for_unknown_email(self) -> None:
        res = await self._request_magic_link("nobody@example.com")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("message", data)
        # No token leakage for non-dev without explicit dev flag
        # (token may be returned in test env — just ensure no error)
        audit = await self._fetch_audit_events()
        self.assertIn("magic_link_requested", audit)

    # ── test 2: request for existing user returns token in test env ──────────

    async def test_request_for_existing_user_creates_challenge(self) -> None:
        await self._register_full_user("existing@example.com")
        res = await self._request_magic_link("existing@example.com")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("message", data)
        # challenge should be in DB
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            row = await conn.fetchrow(
                'SELECT id FROM "03_auth_manage"."12_trx_auth_challenges" '
                'WHERE challenge_type_code = $1 AND consumed_at IS NULL',
                "magic_link",
            )
            self.assertIsNotNone(row)
        finally:
            await conn.close()

    # ── test 3: verify with valid token creates session for existing user ─────

    async def test_verify_creates_session_for_existing_user(self) -> None:
        await self._register_full_user("verify_me@example.com")
        req = await self._request_magic_link("verify_me@example.com")
        token = req.json().get("magic_link_token")
        self.assertIsNotNone(token, "Expected magic_link_token in test environment response")

        res = await self._verify_magic_link(token)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertFalse(data.get("user", {}).get("is_new_user", False), "Should not flag as new user for existing user")

        audit = await self._fetch_audit_events()
        self.assertIn("magic_link_verified", audit)

    # ── test 4: verify auto-creates external_collaborator for new email ───────

    async def test_verify_auto_creates_external_collaborator(self) -> None:
        req = await self._request_magic_link("newbie@example.com")
        token = req.json().get("magic_link_token")
        self.assertIsNotNone(token)

        res = await self._verify_magic_link(token)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertTrue(data.get("user", {}).get("is_new_user"), "Should flag as new user for auto-created user")

        # Check user_category in DB
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            row = await conn.fetchrow(
                'SELECT user_category FROM "03_auth_manage"."03_fct_users" u '
                'JOIN "03_auth_manage"."05_dtl_user_properties" p ON p.user_id = u.id '
                'WHERE p.property_key = $1 AND p.property_value = $2',
                "email",
                "newbie@example.com",
            )
            self.assertIsNotNone(row)
            self.assertEqual(row["user_category"], "external_collaborator")
        finally:
            await conn.close()

        audit = await self._fetch_audit_events()
        self.assertIn("magic_link_external_user_created", audit)

    # ── test 5: verify fails with invalid token ───────────────────────────────

    async def test_verify_rejects_invalid_token(self) -> None:
        res = await self._verify_magic_link("00000000-0000-0000-0000-000000000000.invalidsecret")
        self.assertIn(res.status_code, [400, 401, 422])

    # ── test 6: token is single-use — reuse fails ─────────────────────────────

    async def test_verify_token_single_use(self) -> None:
        req = await self._request_magic_link("singleuse@example.com")
        token = req.json().get("magic_link_token")
        self.assertIsNotNone(token)

        first = await self._verify_magic_link(token)
        self.assertEqual(first.status_code, 200)

        second = await self._verify_magic_link(token)
        self.assertIn(second.status_code, [400, 401, 410])

    # ── test 7: new request expires old challenge ─────────────────────────────

    async def test_new_request_expires_old_challenge(self) -> None:
        await self._request_magic_link("expire@example.com")
        # Second request should expire the first
        req2 = await self._request_magic_link("expire@example.com")
        token2 = req2.json().get("magic_link_token")
        self.assertIsNotNone(token2)

        # Count unconsumed non-expired magic_link challenges for this email
        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM "03_auth_manage"."12_trx_auth_challenges" '
                'WHERE challenge_type_code = $1 AND consumed_at IS NULL AND expires_at > now()',
                "magic_link",
            )
            self.assertEqual(count, 1, "Only one active challenge should exist after re-request")
        finally:
            await conn.close()

    # ── test 8: empty email returns validation error ──────────────────────────

    async def test_request_rejects_empty_email(self) -> None:
        res = await self.client.post("/api/v1/auth/passwordless/request", json={"email": ""})
        self.assertEqual(res.status_code, 422)

    # ── test 9: invalid email format returns validation error ─────────────────

    async def test_request_rejects_malformed_email(self) -> None:
        res = await self.client.post("/api/v1/auth/passwordless/request", json={"email": "not-an-email"})
        self.assertEqual(res.status_code, 422)

    # ── test 10: magic_link account created for existing user ─────────────────

    async def test_magic_link_account_created_for_existing_user(self) -> None:
        await self._register_full_user("fulluser@example.com")
        req = await self._request_magic_link("fulluser@example.com")
        token = req.json().get("magic_link_token")
        res = await self._verify_magic_link(token)
        self.assertEqual(res.status_code, 200)

        conn = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            row = await conn.fetchrow(
                'SELECT ua.account_type_code FROM "03_auth_manage"."08_dtl_user_accounts" ua '
                'JOIN "03_auth_manage"."05_dtl_user_properties" p ON p.user_id = ua.user_id '
                'WHERE p.property_key = $1 AND p.property_value = $2 AND ua.account_type_code = $3',
                "email",
                "fulluser@example.com",
                "magic_link",
            )
            self.assertIsNotNone(row, "magic_link account should be created for full user after first verify")
        finally:
            await conn.close()

    # ── test 11: disabled feature returns 503 ────────────────────────────────

    async def test_disabled_magic_link_returns_503(self) -> None:
        disabled_settings = _base_settings(
            self.postgres.database_dsn,
            run_migrations_on_startup=False,
            magic_link_enabled=False,
        )
        disabled_app = create_app(disabled_settings)
        lifespan = disabled_app.router.lifespan_context(disabled_app)
        await lifespan.__aenter__()
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=disabled_app), base_url="http://testserver")
        try:
            res = await client.post("/api/v1/auth/passwordless/request", json={"email": "test@example.com"})
            self.assertIn(res.status_code, [403, 503])
        finally:
            await client.aclose()
            await lifespan.__aexit__(None, None, None)
