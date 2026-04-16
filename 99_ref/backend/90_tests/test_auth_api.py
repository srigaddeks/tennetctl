from __future__ import annotations

from dataclasses import replace
from importlib import import_module
import logging
from pathlib import Path
from socket import socket
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

import asyncpg
import httpx


application_module = import_module("backend.01_core.application")
settings_module = import_module("backend.00_config.settings")
telemetry_module = import_module("backend.01_core.telemetry")

create_app = application_module.create_app
Settings = settings_module.Settings


class _PostgresTestServer:
    def __init__(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory(prefix="kcontrol-pg-")
        self.base_path = Path(self._temp_dir.name)
        self.data_path = self.base_path / "data"
        self.port = self._find_free_port()
        self.database_name = "kcontrol_auth_test"
        self.admin_dsn = f"postgresql://postgres@127.0.0.1:{self.port}/postgres?sslmode=disable"
        self.database_dsn = f"postgresql://postgres@127.0.0.1:{self.port}/{self.database_name}?sslmode=disable"

    def start(self) -> None:
        subprocess.run(
            [
                shutil.which("initdb") or "initdb",
                "-D",
                str(self.data_path),
                "-A",
                "trust",
                "-U",
                "postgres",
                "--locale=C",
            ],
            check=True,
        )
        subprocess.run(
            [
                shutil.which("pg_ctl") or "pg_ctl",
                "-D",
                str(self.data_path),
                "-o",
                f"-p {self.port}",
                "-w",
                "start",
            ],
            check=True,
        )
        subprocess.run(
            [
                shutil.which("createdb") or "createdb",
                "-h",
                "127.0.0.1",
                "-p",
                str(self.port),
                "-U",
                "postgres",
                self.database_name,
            ],
            check=True,
        )

    def stop(self) -> None:
        try:
            subprocess.run(
                [
                    shutil.which("pg_ctl") or "pg_ctl",
                    "-D",
                    str(self.data_path),
                    "-m",
                    "immediate",
                    "stop",
                ],
                check=True,
            )
        finally:
            self._temp_dir.cleanup()

    @staticmethod
    def _find_free_port() -> int:
        with socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


class AuthApiIntegrationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = _PostgresTestServer()
        cls.postgres.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.postgres.stop()

    async def asyncSetUp(self) -> None:
        await self._reset_schema()
        self.settings = Settings(
            environment="test",
            app_name="kcontrol-auth-test",
            auth_local_core_enabled=True,
            run_migrations_on_startup=True,
            database_url=self.postgres.database_dsn,
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
            migration_directory=Path("backend/01_sql_migrations/01_migrated"),
            otel_enabled=False,
            otel_traces_enabled=False,
            otel_function_trace_enabled=False,
        )
        self.app = create_app(self.settings)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def test_register_login_and_me_flow(self) -> None:
        register_response = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "user@example.com", "password": "StrongPassword123", "username": "user_one"},
        )
        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.headers.get("Cache-Control"), "no-store")

        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "user@example.com", "password": "StrongPassword123"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.headers.get("Cache-Control"), "no-store")
        payload = login_response.json()
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)

        me_response = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {payload['access_token']}"},
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.headers.get("Cache-Control"), "no-store")
        me_payload = me_response.json()
        self.assertEqual(me_payload["email"], "user@example.com")
        self.assertEqual(me_payload["username"], "user_one")

        audit_rows = await self._fetch_audit_rows()
        event_types = [row["event_type"] for row in audit_rows]
        self.assertIn("registered", event_types)
        self.assertIn("login_succeeded", event_types)

    async def test_username_login_and_duplicate_registration_conflict(self) -> None:
        first_response = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "user2@example.com", "password": "StrongPassword123", "username": "user_two"},
        )
        self.assertEqual(first_response.status_code, 201)

        duplicate_response = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "user2@example.com", "password": "StrongPassword123", "username": "user_two_other"},
        )
        self.assertEqual(duplicate_response.status_code, 409)

        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "user_two", "password": "StrongPassword123"},
        )
        self.assertEqual(login_response.status_code, 200)

    async def test_refresh_rotation_and_replay_revokes_session(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "rotate@example.com", "password": "StrongPassword123", "username": "rotator"},
        )
        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "rotator", "password": "StrongPassword123"},
        )
        original_tokens = login_response.json()

        refresh_response = await self.client.post(
            "/api/v1/auth/local/refresh",
            json={"refresh_token": original_tokens["refresh_token"]},
        )
        self.assertEqual(refresh_response.status_code, 200)
        rotated_tokens = refresh_response.json()
        self.assertNotEqual(rotated_tokens["refresh_token"], original_tokens["refresh_token"])

        replay_response = await self.client.post(
            "/api/v1/auth/local/refresh",
            json={"refresh_token": original_tokens["refresh_token"]},
        )
        self.assertEqual(replay_response.status_code, 401)

        audit_rows = await self._fetch_audit_rows()
        event_types = [row["event_type"] for row in audit_rows]
        self.assertIn("refresh_succeeded", event_types)
        self.assertIn("refresh_replay_detected", event_types)

    async def test_logout_revokes_session(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "logout@example.com", "password": "StrongPassword123", "username": "logout_user"},
        )
        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "logout_user", "password": "StrongPassword123"},
        )
        tokens = login_response.json()

        logout_response = await self.client.post(
            "/api/v1/auth/local/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(logout_response.status_code, 200)

        refresh_response = await self.client.post(
            "/api/v1/auth/local/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        self.assertEqual(refresh_response.status_code, 401)

        me_response = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        self.assertEqual(me_response.status_code, 401)

    async def test_forgot_password_and_reset_password(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "reset@example.com", "password": "StrongPassword123", "username": "reset_user"},
        )
        initial_login = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "reset_user", "password": "StrongPassword123"},
        )
        self.assertEqual(initial_login.status_code, 200)
        initial_tokens = initial_login.json()

        forgot_response = await self.client.post(
            "/api/v1/auth/local/forgot-password",
            json={"login": "reset_user"},
        )
        self.assertEqual(forgot_response.status_code, 200)
        reset_token = forgot_response.json()["reset_token"]
        self.assertIsNotNone(reset_token)

        reset_response = await self.client.post(
            "/api/v1/auth/local/reset-password",
            json={"reset_token": reset_token, "new_password": "NewStrongPassword123"},
        )
        self.assertEqual(reset_response.status_code, 200)

        stale_me = await self.client.get(
            "/api/v1/auth/local/me",
            headers={"Authorization": f"Bearer {initial_tokens['access_token']}"},
        )
        self.assertEqual(stale_me.status_code, 401)

        old_login = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "reset_user", "password": "StrongPassword123"},
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "reset_user", "password": "NewStrongPassword123"},
        )
        self.assertEqual(new_login.status_code, 200)

    async def test_second_password_reset_request_invalidates_the_first_token(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "second-reset@example.com", "password": "StrongPassword123", "username": "second_reset"},
        )
        first_forgot = await self.client.post(
            "/api/v1/auth/local/forgot-password",
            json={"login": "second_reset"},
        )
        second_forgot = await self.client.post(
            "/api/v1/auth/local/forgot-password",
            json={"login": "second_reset"},
        )
        first_token = first_forgot.json()["reset_token"]
        second_token = second_forgot.json()["reset_token"]

        self.assertNotEqual(first_token, second_token)

        first_reset = await self.client.post(
            "/api/v1/auth/local/reset-password",
            json={"reset_token": first_token, "new_password": "AnotherStrongPassword123"},
        )
        self.assertEqual(first_reset.status_code, 401)

        second_reset = await self.client.post(
            "/api/v1/auth/local/reset-password",
            json={"reset_token": second_token, "new_password": "AnotherStrongPassword123"},
        )
        self.assertEqual(second_reset.status_code, 200)

    async def test_function_trace_logs_redact_sensitive_values(self) -> None:
        records: list[logging.LogRecord] = []
        trace_settings = replace(
            self.settings,
            app_name="kcontrol-auth-test-trace",
            otel_enabled=True,
            otel_traces_enabled=True,
            otel_function_trace_enabled=True,
        )
        trace_app = create_app(trace_settings)
        trace_lifespan = trace_app.router.lifespan_context(trace_app)
        await trace_lifespan.__aenter__()
        trace_client = httpx.AsyncClient(transport=httpx.ASGITransport(app=trace_app), base_url="http://testserver")

        class _ListHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        handler = _ListHandler(level=logging.INFO)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            response = await trace_client.post(
                "/api/v1/auth/local/register",
                json={"email": "trace@example.com", "password": "StrongPassword123", "username": "trace_user"},
            )
            self.assertEqual(response.status_code, 201)
        finally:
            root_logger.removeHandler(handler)
            await trace_client.aclose()
            await trace_lifespan.__aexit__(None, None, None)
            sys.setprofile(None)
            threading.setprofile(None)
            telemetry_module._FUNCTION_PROFILER_STARTED = False

        # The profiler logs non-decorated functions; decorated functions (like
        # AuthService methods) are logged by @instrument_function instead.
        # Check that SOME profiler call/return records exist (for non-decorated code)
        function_call_records = [
            record for record in records if getattr(record, "action", None) == "python.function.call"
        ]
        function_return_records = [
            record for record in records if getattr(record, "action", None) == "python.function.return"
        ]
        self.assertTrue(function_call_records)
        self.assertTrue(function_return_records)

        # AuthService.register_user is decorated with @instrument_class_methods,
        # so it emits via the decorator (action=auth.service.register_user), not
        # the profiler (action=python.function.call). The profiler skips it to
        # prevent duplicate logging.
        decorator_started = [
            record for record in records
            if getattr(record, "action", None) == "auth.service.register_user"
            and getattr(record, "outcome", None) == "started"
        ]
        decorator_completed = [
            record for record in records
            if getattr(record, "action", None) == "auth.service.register_user"
            and getattr(record, "outcome", None) == "success"
        ]
        self.assertTrue(decorator_started, "Expected decorator-based started log for register_user")
        self.assertTrue(decorator_completed, "Expected decorator-based completed log for register_user")

        service_call = decorator_started[0]
        service_return = decorator_completed[0]

        payload = getattr(service_call, "arguments", {})
        self.assertEqual(payload["payload"]["password"], "[REDACTED]")
        self.assertIn("register_user", getattr(service_call, "qualified_name", ""))
        self.assertIsNotNone(getattr(service_return, "result", None))

    async def test_feature_flag_disables_public_auth_endpoints(self) -> None:
        register_response = await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "blocked@example.com", "password": "StrongPassword123", "username": "blocked_user"},
        )
        self.assertEqual(register_response.status_code, 201)

        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "blocked_user", "password": "StrongPassword123"},
        )
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.json()["access_token"]

        disabled_settings = Settings(
            environment="test",
            app_name="kcontrol-auth-test-disabled",
            auth_local_core_enabled=False,
            run_migrations_on_startup=False,
            database_url=self.postgres.database_dsn,
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
            migration_directory=self.settings.migration_directory,
        )
        disabled_app = create_app(disabled_settings)
        lifespan = disabled_app.router.lifespan_context(disabled_app)
        await lifespan.__aenter__()
        disabled_client = httpx.AsyncClient(transport=httpx.ASGITransport(app=disabled_app), base_url="http://testserver")
        try:
            response = await disabled_client.post(
                "/api/v1/auth/local/register",
                json={"email": "blocked@example.com", "password": "StrongPassword123", "username": "blocked_user"},
            )
            self.assertEqual(response.status_code, 503)

            me_response = await disabled_client.get(
                "/api/v1/auth/local/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            self.assertEqual(me_response.status_code, 503)
        finally:
            await disabled_client.aclose()
            await lifespan.__aexit__(None, None, None)

    async def test_user_properties_crud(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "props@example.com", "password": "StrongPassword123", "username": "props_user"},
        )
        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "props_user", "password": "StrongPassword123"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # GET /me/properties — should return seeded properties (email, username)
        props_response = await self.client.get("/api/v1/auth/local/me/properties", headers=headers)
        self.assertEqual(props_response.status_code, 200)
        props = props_response.json()
        self.assertIn("properties", props)
        keys = {p["key"] for p in props["properties"]}
        self.assertIn("email", keys)
        self.assertIn("username", keys)

        # PUT /me/properties/timezone — set a new property
        set_response = await self.client.put(
            "/api/v1/auth/local/me/properties/timezone",
            json={"value": "Asia/Kolkata"},
            headers=headers,
        )
        self.assertEqual(set_response.status_code, 200)
        self.assertEqual(set_response.json()["key"], "timezone")
        self.assertEqual(set_response.json()["value"], "Asia/Kolkata")

        # GET again — timezone should be present
        props_response = await self.client.get("/api/v1/auth/local/me/properties", headers=headers)
        keys = {p["key"] for p in props_response.json()["properties"]}
        self.assertIn("timezone", keys)

        # DELETE /me/properties/timezone
        delete_response = await self.client.delete(
            "/api/v1/auth/local/me/properties/timezone",
            headers=headers,
        )
        self.assertEqual(delete_response.status_code, 204)

        # GET again — timezone should be gone
        props_response = await self.client.get("/api/v1/auth/local/me/properties", headers=headers)
        keys = {p["key"] for p in props_response.json()["properties"]}
        self.assertNotIn("timezone", keys)

    async def test_user_accounts_list(self) -> None:
        await self.client.post(
            "/api/v1/auth/local/register",
            json={"email": "accts@example.com", "password": "StrongPassword123", "username": "accts_user"},
        )
        login_response = await self.client.post(
            "/api/v1/auth/local/login",
            json={"login": "accts_user", "password": "StrongPassword123"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # GET /me/accounts — should return at least local_password account
        accounts_response = await self.client.get("/api/v1/auth/local/me/accounts", headers=headers)
        self.assertEqual(accounts_response.status_code, 200)
        accounts = accounts_response.json()
        self.assertIn("accounts", accounts)
        self.assertTrue(len(accounts["accounts"]) >= 1)
        account_types = {a["account_type"] for a in accounts["accounts"]}
        self.assertIn("local_password", account_types)
        # Secret properties (password_hash) should NOT be exposed
        for account in accounts["accounts"]:
            self.assertNotIn("password_hash", account.get("properties", {}))

    async def test_probes_and_auth_routes_are_registered(self) -> None:
        paths = {route.path for route in self.app.routes}
        self.assertIn("/api/v1/auth/local/register", paths)
        self.assertIn("/api/v1/auth/local/login", paths)
        self.assertIn("/api/v1/auth/local/refresh", paths)
        self.assertIn("/api/v1/auth/local/logout", paths)
        self.assertIn("/api/v1/auth/local/me", paths)
        self.assertIn("/livez", paths)
        self.assertIn("/readyz", paths)
        self.assertIn("/healthz", paths)

        live_response = await self.client.get("/livez")
        self.assertEqual(live_response.status_code, 200)
        self.assertEqual(live_response.json(), {"status": "ok"})

        ready_response = await self.client.get("/readyz")
        self.assertEqual(ready_response.status_code, 200)
        self.assertEqual(ready_response.json(), {"status": "ok"})

        health_response = await self.client.get("/healthz")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json(), {"status": "ok"})

    async def _fetch_audit_rows(self):
        connection = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            return await connection.fetch('SELECT event_type FROM "03_auth_manage"."40_aud_events" ORDER BY occurred_at ASC')
        finally:
            await connection.close()

    async def _reset_schema(self) -> None:
        connection = await asyncpg.connect(dsn=self.postgres.database_dsn)
        try:
            await connection.execute('DROP SCHEMA IF EXISTS "03_auth_manage" CASCADE')
            await connection.execute('DROP SCHEMA IF EXISTS "01_dev_features" CASCADE')
        finally:
            await connection.close()
