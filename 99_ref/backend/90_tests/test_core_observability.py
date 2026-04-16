from __future__ import annotations

from contextlib import asynccontextmanager, nullcontext
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI


audit_module = import_module("backend.01_core.audit")
database_module = import_module("backend.01_core.database")
errors_module = import_module("backend.01_core.errors")
telemetry_module = import_module("backend.01_core.telemetry")
time_utils_module = import_module("backend.01_core.time_utils")
permission_check_module = import_module("backend.03_auth_manage._permission_check")
jwt_codec_module = import_module("backend.03_auth_manage.01_authlib.jwt_codec")
refresh_tokens_module = import_module("backend.03_auth_manage.02_token_gen.refresh_tokens")
feature_flags_repository_module = import_module("backend.03_auth_manage.03_feature_flags.repository")

AuditEntry = audit_module.AuditEntry
AuditWriter = audit_module.AuditWriter
AppError = errors_module.AppError
DatabasePool = database_module.DatabasePool
InstrumentedAPIRouter = telemetry_module.InstrumentedAPIRouter
instrument_class_methods = telemetry_module.instrument_class_methods
instrument_function = telemetry_module.instrument_function
instrument_module_functions = telemetry_module.instrument_module_functions
JWTCodec = jwt_codec_module.JWTCodec
RefreshTokenManager = refresh_tokens_module.RefreshTokenManager
FeatureFlagRepository = feature_flags_repository_module.FeatureFlagRepository


class _FakeTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.execute = AsyncMock()
        self.fetch = AsyncMock(return_value=[])

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction()


class _AcquireContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeAsyncpgPool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection
        self.closed = False

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)

    async def close(self) -> None:
        self.closed = True


class _FakeMigrationPool:
    def __init__(self) -> None:
        self.lock_connection = _FakeConnection()
        self.tx_connection = _FakeConnection()

    @asynccontextmanager
    async def acquire(self):
        yield self.lock_connection

    @asynccontextmanager
    async def transaction(self):
        yield self.tx_connection


class _FakePermissionConnection:
    def __init__(self) -> None:
        self.fetchrow = AsyncMock(return_value={"ok": 1})


class _FakeRepositoryConnection:
    def __init__(self) -> None:
        self.fetch = AsyncMock(return_value=[])


class CoreObservabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_instrument_function_wraps_async_function(self) -> None:
        with (
            patch.object(telemetry_module, "start_operation_span", return_value=nullcontext()) as span_mock,
            patch.object(telemetry_module, "get_logger") as get_logger_mock,
        ):
            logger = get_logger_mock.return_value

            @instrument_function(span_name="demo.fn", logger_name="backend.test.instrumentation")
            async def demo_function(password: str) -> str:
                return password

            result = await demo_function(password="secret-value")

        self.assertEqual(result, "secret-value")
        span_mock.assert_called_once()
        self.assertEqual(logger.info.call_count, 2)
        started_payload = logger.info.call_args_list[0].kwargs["extra"]
        self.assertEqual(started_payload["arguments"]["password"], "[REDACTED]")

    async def test_instrument_class_methods_wraps_public_methods(self) -> None:
        with patch.object(telemetry_module, "start_operation_span", return_value=nullcontext()) as span_mock:

            @instrument_class_methods(namespace="demo.service")
            class DemoService:
                async def run(self, token: str) -> str:
                    return token

            service = DemoService()
            result = await service.run("secret-token")

        self.assertEqual(result, "secret-token")
        span_mock.assert_called_once()
        self.assertEqual(span_mock.call_args.args[0], "demo.service.run")

    async def test_instrument_module_functions_wraps_module_level_functions(self) -> None:
        async def demo_helper(api_key: str) -> str:
            return api_key

        demo_helper.__module__ = "demo.module"
        module_globals = {"__name__": "demo.module", "demo_helper": demo_helper}

        with patch.object(telemetry_module, "start_operation_span", return_value=nullcontext()) as span_mock:
            instrument_module_functions(module_globals, namespace="demo.module")
            result = await module_globals["demo_helper"](api_key="secret-key")

        self.assertEqual(result, "secret-key")
        span_mock.assert_called_once()
        self.assertEqual(span_mock.call_args.args[0], "demo.module.demo_helper")

    async def test_instrumented_api_router_wraps_endpoint(self) -> None:
        router = InstrumentedAPIRouter(prefix="/demo", tags=["demo"])

        @router.get("/ping")
        async def ping() -> dict[str, str]:
            return {"status": "ok"}

        app = FastAPI()
        app.include_router(router)

        with (
            patch.object(telemetry_module, "start_operation_span", return_value=nullcontext()) as span_mock,
            patch.object(telemetry_module, "get_logger") as get_logger_mock,
        ):
            client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")
            try:
                response = await client.get("/demo/ping")
            finally:
                await client.aclose()

        self.assertEqual(response.status_code, 200)
        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("fastapi.endpoint.ping", span_names)

    async def test_audit_writer_uses_span_and_log(self) -> None:
        entry = AuditEntry(
            id="evt-1",
            tenant_key="default",
            entity_type="user",
            entity_id="user-1",
            event_type="created",
            event_category="auth",
            occurred_at=datetime.now(tz=UTC),
            actor_id="actor-1",
            actor_type="user",
            properties={"status": "active"},
        )
        connection = AsyncMock()
        writer = AuditWriter(schema_name="test_schema")

        with (
            patch.object(audit_module, "start_operation_span", return_value=nullcontext()) as span_mock,
            patch.object(audit_module._LOGGER, "info") as log_mock,
        ):
            await writer.write_entry(connection, entry)

        span_mock.assert_called_once()
        log_mock.assert_called_once()
        connection.execute.assert_awaited()

    async def test_database_pool_methods_emit_spans(self) -> None:
        fake_connection = _FakeConnection()
        fake_pool = _FakeAsyncpgPool(fake_connection)
        pool = DatabasePool(
            database_url="postgresql://example/test",
            min_size=1,
            max_size=2,
            command_timeout_seconds=30,
            application_name="kcontrol-test",
        )

        with (
            patch.object(database_module, "start_operation_span", side_effect=lambda *args, **kwargs: nullcontext()) as span_mock,
            patch.object(database_module.asyncpg, "create_pool", AsyncMock(return_value=fake_pool)),
            patch.object(database_module._LOGGER, "info"),
        ):
            await pool.open()
            async with pool.transaction() as connection:
                await connection.execute("SELECT 2")
            await pool.ping()
            await pool.close()

        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("db.pool.open", span_names)
        self.assertIn("db.transaction", span_names)
        self.assertIn("db.ping", span_names)
        self.assertIn("db.pool.close", span_names)
        self.assertTrue(fake_pool.closed)

    async def test_apply_sql_migrations_emits_spans(self) -> None:
        migration_pool = _FakeMigrationPool()
        with TemporaryDirectory() as temp_dir:
            migration_dir = Path(temp_dir)
            (migration_dir / "20260101_create_table.sql").write_text(
                "CREATE TABLE sample(id INT);",
                encoding="utf-8",
            )

            with (
                patch.object(
                    database_module,
                    "start_operation_span",
                    side_effect=lambda *args, **kwargs: nullcontext(),
                ) as span_mock,
                patch.object(database_module._LOGGER, "info"),
            ):
                await database_module.apply_sql_migrations(
                    migration_pool,
                    migration_dir,
                    dry_run=True,
                )

        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("db.migrations.apply", span_names)
        self.assertIn("db.migration.execute", span_names)

    async def test_app_error_creation_emits_span_and_log(self) -> None:
        with (
            patch.object(errors_module, "start_operation_span", return_value=nullcontext()) as span_mock,
            patch.object(errors_module._LOGGER, "info") as log_mock,
        ):
            error = AppError(status_code=409, code="conflict", message="Conflict.")

        self.assertEqual(str(error), "Conflict.")
        span_mock.assert_called_once()
        log_mock.assert_called_once()

    async def test_time_utils_emit_spans(self) -> None:
        value = datetime(2026, 3, 13, 12, 0, tzinfo=UTC)
        with patch.object(
            time_utils_module,
            "start_operation_span",
            side_effect=lambda *args, **kwargs: nullcontext(),
        ) as span_mock:
            now_value = time_utils_module.utc_now_sql()
            sql_value = time_utils_module.to_sql_timestamp(value)
            restored_value = time_utils_module.from_sql_timestamp(sql_value)

        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("time.utc_now_sql", span_names)
        self.assertIn("time.to_sql_timestamp", span_names)
        self.assertIn("time.from_sql_timestamp", span_names)
        self.assertIsNone(now_value.tzinfo)
        self.assertIsNone(sql_value.tzinfo)
        self.assertEqual(restored_value.tzinfo, UTC)

    async def test_permission_check_emits_span(self) -> None:
        connection = _FakePermissionConnection()

        with patch.object(
            telemetry_module,
            "start_operation_span",
            side_effect=lambda *args, **kwargs: nullcontext(),
        ) as span_mock:
            await permission_check_module.require_permission(
                connection,
                "user-1",
                "feature_flag_registry.view",
            )

        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("auth.permission_check.require_permission", span_names)

    async def test_auth_token_helpers_emit_spans(self) -> None:
        jwt_codec = JWTCodec(
            secret="test-secret",
            algorithm="HS256",
            issuer="kcontrol-test",
            audience="kcontrol-api",
            ttl_seconds=300,
        )
        refresh_manager = RefreshTokenManager()

        with patch.object(
            telemetry_module,
            "start_operation_span",
            side_effect=lambda *args, **kwargs: nullcontext(),
        ) as span_mock:
            encoded = jwt_codec.encode_access_token(
                subject="user-1",
                session_id="session-1",
                tenant_key="default",
            )
            claims = jwt_codec.decode_access_token(encoded.token)
            refresh_token = refresh_manager.generate("session-1")
            refresh_parts = refresh_manager.parse(refresh_token)
            refresh_hash = refresh_manager.hash_secret(refresh_parts.secret)

        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("auth.jwt_codec.encode_access_token", span_names)
        self.assertIn("auth.jwt_codec.decode_access_token", span_names)
        self.assertIn("auth.refresh_tokens.generate", span_names)
        self.assertIn("auth.refresh_tokens.parse", span_names)
        self.assertIn("auth.refresh_tokens.hash_secret", span_names)
        self.assertEqual(claims["sub"], "user-1")
        self.assertEqual(refresh_parts.session_id, "session-1")
        self.assertTrue(refresh_hash)

    async def test_repository_methods_emit_spans(self) -> None:
        repository = FeatureFlagRepository()
        connection = _FakeRepositoryConnection()

        with patch.object(
            telemetry_module,
            "start_operation_span",
            side_effect=lambda *args, **kwargs: nullcontext(),
        ) as span_mock:
            result = await repository.list_categories(connection)

        self.assertEqual(result, [])
        span_names = [call.args[0] for call in span_mock.call_args_list]
        self.assertIn("feature_flags.repository.list_categories", span_names)
