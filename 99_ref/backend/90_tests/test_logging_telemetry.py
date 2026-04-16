from __future__ import annotations

from contextlib import nullcontext
from importlib import import_module
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json
import logging
import unittest

import httpx
from fastapi import FastAPI

logging_module = import_module("backend.01_core.logging_utils")
telemetry_module = import_module("backend.01_core.telemetry")
application_module = import_module("backend.01_core.application")
settings_module = import_module("backend.00_config.settings")

ContextEnricher = logging_module.ContextEnricher
JsonFormatter = logging_module.JsonFormatter
TextFormatter = logging_module.TextFormatter
bind_request_context = logging_module.bind_request_context
reset_request_context = logging_module.reset_request_context
bind_actor_context = logging_module.bind_actor_context
reset_actor_context = logging_module.reset_actor_context
configure_logging = logging_module.configure_logging
get_logger = logging_module.get_logger
Settings = settings_module.Settings


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        environment="test",
        app_name="kcontrol-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=False,
        database_url="postgresql://localhost/test",
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-secret",
        access_token_algorithm="HS256",
        access_token_issuer="kcontrol-test",
        access_token_audience="kcontrol-test-api",
        access_token_ttl_seconds=900,
        refresh_token_ttl_seconds=86400,
        brute_force_window_seconds=900,
        brute_force_max_attempts=5,
        default_tenant_key="default",
        trust_proxy_headers=False,
        trusted_proxy_depth=1,
        migration_directory=Path("/nonexistent"),
    )
    defaults.update(overrides)
    return Settings(**defaults)


class LoggingConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_handlers = logging.getLogger().handlers[:]
        self._original_level = logging.getLogger().level

    def tearDown(self) -> None:
        root = logging.getLogger()
        for handler in root.handlers[:]:
            if hasattr(handler, "_kcontrol_json_handler") or hasattr(handler, "_kcontrol_text_handler"):
                root.removeHandler(handler)
        root.handlers = self._original_handlers
        root.setLevel(self._original_level)

    def test_configure_logging_applies_root_level_from_settings(self) -> None:
        settings = _make_settings(log_level="DEBUG", log_format="json")
        # Remove existing kcontrol handlers to allow reconfiguration
        root = logging.getLogger()
        for handler in root.handlers[:]:
            if hasattr(handler, "_kcontrol_json_handler") or hasattr(handler, "_kcontrol_text_handler"):
                root.removeHandler(handler)
        configure_logging(settings)
        self.assertEqual(root.level, logging.DEBUG)

    def test_configure_logging_applies_per_module_overrides(self) -> None:
        settings = _make_settings(
            log_level="INFO",
            log_format="json",
            log_level_overrides={"backend.test_override": "DEBUG"},
        )
        root = logging.getLogger()
        for handler in root.handlers[:]:
            if hasattr(handler, "_kcontrol_json_handler") or hasattr(handler, "_kcontrol_text_handler"):
                root.removeHandler(handler)
        configure_logging(settings)
        override_logger = logging.getLogger("backend.test_override")
        self.assertEqual(override_logger.level, logging.DEBUG)
        self.assertEqual(root.level, logging.INFO)

    def test_text_formatter_renders_readable_output(self) -> None:
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="backend.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.service = "kcontrol-test"
        record.request_id = "abcdef1234567890"
        record.actor_id = "user-12345678"
        output = formatter.format(record)
        self.assertIn("Test message", output)
        self.assertIn("[kcontrol-test]", output)
        self.assertIn("[req:abcdef12]", output)
        self.assertIn("[actor:user-123]", output)
        self.assertNotIn("{", output)

    def test_text_formatter_without_context(self) -> None:
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="backend.test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Bare message",
            args=(),
            exc_info=None,
        )
        record.service = None
        record.request_id = None
        record.actor_id = None
        output = formatter.format(record)
        self.assertIn("Bare message", output)
        self.assertIn("WARNING", output)


class ActorContextTests(unittest.TestCase):
    def test_actor_id_context_binding_appears_in_log_records(self) -> None:
        enricher = ContextEnricher()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        token = bind_actor_context("user-abc-123")
        try:
            enricher.filter(record)
            self.assertEqual(record.actor_id, "user-abc-123")
        finally:
            reset_actor_context(token)

    def test_actor_id_defaults_to_none(self) -> None:
        enricher = ContextEnricher()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        enricher.filter(record)
        self.assertIsNone(record.actor_id)


class JsonFormatterTests(unittest.TestCase):
    def test_json_formatter_includes_actor_id_and_request_id(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="backend.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test log entry",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-1234"
        record.actor_id = "user-5678"
        record.service = "kcontrol-test"
        record.environment = "test"
        record.trace_id = None
        record.span_id = None
        record.action = "test.action"
        record.outcome = "success"

        output = formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["request_id"], "req-1234")
        self.assertEqual(data["actor_id"], "user-5678")
        self.assertEqual(data["service"], "kcontrol-test")
        self.assertEqual(data["message"], "Test log entry")

    def test_json_formatter_redacts_sensitive_keys(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="backend.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="login attempt",
            args=(),
            exc_info=None,
        )
        record.password = "super-secret"
        record.access_token = "jwt-token-value"
        record.request_id = None
        record.actor_id = None
        record.service = None
        record.environment = None
        record.trace_id = None
        record.span_id = None
        record.action = "auth.login"
        record.outcome = "success"

        output = formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["password"], "[REDACTED]")
        self.assertEqual(data["access_token"], "[REDACTED]")

    def test_json_formatter_includes_exception_info(self) -> None:
        formatter = JsonFormatter()
        try:
            raise ValueError("test error for formatter")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="backend.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Something failed",
            args=(),
            exc_info=exc_info,
        )
        record.request_id = None
        record.actor_id = None
        record.service = None
        record.environment = None
        record.trace_id = None
        record.span_id = None
        record.action = "test.error"
        record.outcome = "error"

        output = formatter.format(record)
        data = json.loads(output)
        self.assertIn("exception", data)
        self.assertEqual(data["exception"]["type"], "ValueError")
        self.assertIn("test error for formatter", data["exception"]["message"])
        self.assertIn("traceback", data["exception"])


ECSFormatter = logging_module.ECSFormatter
CEFFormatter = logging_module.CEFFormatter
SyslogFormatter = logging_module.SyslogFormatter
get_formatter = logging_module.get_formatter


class ECSFormatterTests(unittest.TestCase):
    def _make_record(self, **kwargs) -> logging.LogRecord:
        record = logging.LogRecord(
            name="backend.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test ECS message",
            args=(),
            exc_info=None,
        )
        record.service = "kcontrol-test"
        record.environment = "test"
        record.request_id = "req-ecs-123"
        record.actor_id = "user-ecs-456"
        record.trace_id = "00000000000000000000000000abcdef"
        record.span_id = "00000000abcdef01"
        record.action = "test.action"
        record.outcome = "success"
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def test_ecs_formatter_produces_valid_json(self) -> None:
        formatter = ECSFormatter()
        output = formatter.format(self._make_record())
        data = json.loads(output)
        self.assertEqual(data["ecs.version"], "8.11.0")
        self.assertIn("@timestamp", data)
        self.assertEqual(data["log.level"], "info")
        self.assertEqual(data["message"], "Test ECS message")
        self.assertEqual(data["service.name"], "kcontrol-test")
        self.assertEqual(data["trace.id"], "00000000000000000000000000abcdef")
        self.assertEqual(data["span.id"], "00000000abcdef01")
        self.assertEqual(data["user.id"], "user-ecs-456")
        self.assertEqual(data["http.request.id"], "req-ecs-123")

    def test_ecs_formatter_handles_exception(self) -> None:
        formatter = ECSFormatter()
        try:
            raise ValueError("ecs test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = self._make_record()
        record.exc_info = exc_info
        output = formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["error.type"], "ValueError")
        self.assertIn("ecs test error", data["error.message"])
        self.assertIn("error.stack_trace", data)


class CEFFormatterTests(unittest.TestCase):
    def _make_record(self, **kwargs) -> logging.LogRecord:
        record = logging.LogRecord(
            name="backend.test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="CEF test event",
            args=(),
            exc_info=None,
        )
        record.service = "kcontrol-test"
        record.environment = "test"
        record.request_id = "req-cef-789"
        record.actor_id = "user-cef-012"
        record.trace_id = "aabbccdd"
        record.span_id = None
        record.action = "auth.login"
        record.outcome = "success"
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def test_cef_formatter_produces_valid_cef_header(self) -> None:
        formatter = CEFFormatter()
        output = formatter.format(self._make_record())
        self.assertTrue(output.startswith("CEF:0|"))
        parts = output.split("|")
        self.assertEqual(parts[0], "CEF:0")
        self.assertEqual(parts[1], "Kreesalis")
        self.assertEqual(parts[2], "kcontrol")
        self.assertEqual(parts[3], "1.0")
        # Severity should be 5 for WARNING
        self.assertEqual(parts[6].split("|")[0], "5")

    def test_cef_formatter_includes_extensions(self) -> None:
        formatter = CEFFormatter()
        output = formatter.format(self._make_record())
        self.assertIn("cs1=req-cef-789", output)
        self.assertIn("cs1Label=RequestID", output)
        self.assertIn("duser=user-cef-012", output)
        self.assertIn("cs2=aabbccdd", output)
        self.assertIn("cs2Label=TraceID", output)
        self.assertIn("outcome=success", output)

    def test_cef_formatter_escapes_special_characters(self) -> None:
        formatter = CEFFormatter()
        record = self._make_record()
        record.msg = "test=with|special\\chars"
        record.args = ()
        output = formatter.format(record)
        self.assertIn("msg=test\\=with|special\\\\chars", output)


class SyslogFormatterTests(unittest.TestCase):
    def _make_record(self, **kwargs) -> logging.LogRecord:
        record = logging.LogRecord(
            name="backend.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Syslog test message",
            args=(),
            exc_info=None,
        )
        record.service = "kcontrol-test"
        record.environment = "production"
        record.request_id = "req-sys-111"
        record.actor_id = "user-sys-222"
        record.trace_id = "trace-id-333"
        record.span_id = "span-444"
        record.action = "db.query"
        record.outcome = "error"
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def test_syslog_formatter_produces_rfc5424_structure(self) -> None:
        formatter = SyslogFormatter(app_name="kcontrol-test")
        output = formatter.format(self._make_record())
        # PRI for facility=1 (user), severity=3 (error): (1*8)+3 = 11
        self.assertTrue(output.startswith("<11>1 "))
        self.assertIn("kcontrol-test", output)
        self.assertIn("Syslog test message", output)

    def test_syslog_formatter_includes_structured_data(self) -> None:
        formatter = SyslogFormatter()
        output = formatter.format(self._make_record())
        self.assertIn('[kcontrol@49610', output)
        self.assertIn('requestId="req-sys-111"', output)
        self.assertIn('actorId="user-sys-222"', output)
        self.assertIn('traceId="trace-id-333"', output)
        self.assertIn('spanId="span-444"', output)
        self.assertIn('outcome="error"', output)
        self.assertIn('env="production"', output)

    def test_syslog_formatter_handles_no_context(self) -> None:
        formatter = SyslogFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="bare message",
            args=(),
            exc_info=None,
        )
        record.service = None
        record.environment = None
        record.request_id = None
        record.actor_id = None
        record.trace_id = None
        record.span_id = None
        record.action = None
        record.outcome = None
        output = formatter.format(record)
        self.assertIn("bare message", output)
        # No structured data, should have "-"
        self.assertIn(" - bare message", output)


class FormatterRegistryTests(unittest.TestCase):
    def test_get_formatter_returns_known_formats(self) -> None:
        for fmt_name in ("json", "text", "ecs", "cef", "syslog"):
            formatter = get_formatter(fmt_name)
            self.assertIsInstance(formatter, logging.Formatter)

    def test_get_formatter_raises_on_unknown(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            get_formatter("xml")
        self.assertIn("xml", str(ctx.exception))
        self.assertIn("Supported", str(ctx.exception))


class UnhandledExceptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_unhandled_exception_returns_safe_500_response(self) -> None:
        settings = _make_settings()

        with (
            patch.object(application_module, "start_operation_span", return_value=nullcontext()),
            patch.object(application_module, "configure_observability"),
            patch.object(application_module, "instrument_fastapi_app"),
        ):
            app = application_module.create_app(settings)

        @app.get("/test-crash")
        async def crash_endpoint():
            raise RuntimeError("Internal secret details about the database")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/test-crash")

        self.assertEqual(response.status_code, 500)
        body = response.text
        self.assertNotIn("Internal secret details", body)

    async def test_app_error_handler_returns_structured_error(self) -> None:
        _errors_mod = import_module("backend.01_core.errors")
        _AppError = _errors_mod.AppError

        settings = _make_settings()

        with (
            patch.object(application_module, "start_operation_span", return_value=nullcontext()),
            patch.object(application_module, "configure_observability"),
            patch.object(application_module, "instrument_fastapi_app"),
        ):
            app = application_module.create_app(settings)

        @app.get("/test-app-error")
        async def app_error_endpoint():
            raise _AppError(status_code=409, code="conflict", message="Resource conflict.")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/test-app-error")

        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data["error"]["code"], "conflict")
        self.assertEqual(data["error"]["message"], "Resource conflict.")


class ObservabilityShutdownTests(unittest.TestCase):
    def test_shutdown_observability_calls_flush_and_shutdown(self) -> None:
        mock_tracer = MagicMock()
        mock_logger = MagicMock()
        mock_meter = MagicMock()

        with (
            patch.object(telemetry_module, "_tracer_provider", mock_tracer),
            patch.object(telemetry_module, "_logger_provider", mock_logger),
            patch.object(telemetry_module, "_meter_provider", mock_meter),
        ):
            telemetry_module.shutdown_observability()

        mock_tracer.force_flush.assert_called_once_with(timeout_millis=5_000)
        mock_tracer.shutdown.assert_called_once()
        mock_logger.force_flush.assert_called_once_with(timeout_millis=5_000)
        mock_logger.shutdown.assert_called_once()
        mock_meter.force_flush.assert_called_once_with(timeout_millis=5_000)
        mock_meter.shutdown.assert_called_once()

    def test_shutdown_observability_handles_none_providers(self) -> None:
        with (
            patch.object(telemetry_module, "_tracer_provider", None),
            patch.object(telemetry_module, "_logger_provider", None),
            patch.object(telemetry_module, "_meter_provider", None),
        ):
            telemetry_module.shutdown_observability()


class SettingsValidationTests(unittest.TestCase):
    def test_log_level_validation_rejects_invalid(self) -> None:
        with self.assertRaises(ValueError):
            settings_module._read_log_level("FAKE_LOG_LEVEL", default="INVALID")

    def test_log_level_validation_accepts_valid(self) -> None:
        import os
        os.environ["_TEST_LOG_LEVEL"] = "DEBUG"
        try:
            result = settings_module._read_log_level("_TEST_LOG_LEVEL", default="INFO")
            self.assertEqual(result, "DEBUG")
        finally:
            del os.environ["_TEST_LOG_LEVEL"]

    def test_log_format_validation_rejects_invalid(self) -> None:
        with self.assertRaises(ValueError):
            settings_module._read_log_format("FAKE_LOG_FORMAT", default="xml")

    def test_log_format_validation_accepts_all_supported_formats(self) -> None:
        import os
        for fmt in ("json", "text", "ecs", "cef", "syslog"):
            os.environ["_TEST_LOG_FORMAT"] = fmt
            try:
                result = settings_module._read_log_format("_TEST_LOG_FORMAT", default="json")
                self.assertEqual(result, fmt)
            finally:
                del os.environ["_TEST_LOG_FORMAT"]

    def test_log_level_overrides_parsing(self) -> None:
        import os
        os.environ["_TEST_OVERRIDES"] = "backend.auth=DEBUG,backend.database=WARNING"
        try:
            result = settings_module._read_log_level_overrides("_TEST_OVERRIDES")
            self.assertEqual(result, {"backend.auth": "DEBUG", "backend.database": "WARNING"})
        finally:
            del os.environ["_TEST_OVERRIDES"]

    def test_log_level_overrides_rejects_invalid_level(self) -> None:
        import os
        os.environ["_TEST_BAD_OVERRIDES"] = "backend.auth=VERBOSE"
        try:
            with self.assertRaises(ValueError):
                settings_module._read_log_level_overrides("_TEST_BAD_OVERRIDES")
        finally:
            del os.environ["_TEST_BAD_OVERRIDES"]

    def test_log_level_overrides_empty_returns_empty_dict(self) -> None:
        result = settings_module._read_log_level_overrides("_NONEXISTENT_ENV_VAR")
        self.assertEqual(result, {})
