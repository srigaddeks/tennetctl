"""Tests for observability enhancements: session context, route resolution,
function metrics accumulator, instrumentation dedup, and GlitchTip integration."""

from __future__ import annotations

from contextlib import nullcontext
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, patch
import json
import logging
import threading
import time
import unittest

logging_module = import_module("backend.01_core.logging_utils")
telemetry_module = import_module("backend.01_core.telemetry")
settings_module = import_module("backend.00_config.settings")

ContextEnricher = logging_module.ContextEnricher
JsonFormatter = logging_module.JsonFormatter
ECSFormatter = logging_module.ECSFormatter
CEFFormatter = logging_module.CEFFormatter
SyslogFormatter = logging_module.SyslogFormatter
TextFormatter = logging_module.TextFormatter
bind_session_context = logging_module.bind_session_context
reset_session_context = logging_module.reset_session_context
bind_actor_context = logging_module.bind_actor_context
reset_actor_context = logging_module.reset_actor_context
bind_request_context = logging_module.bind_request_context
reset_request_context = logging_module.reset_request_context
Settings = settings_module.Settings

_FunctionCallAccumulator = telemetry_module._FunctionCallAccumulator
_INSTRUMENTED_MARKER = telemetry_module._INSTRUMENTED_MARKER


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


def _make_record(**kwargs) -> logging.LogRecord:
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
    record.environment = "test"
    record.request_id = "req-123"
    record.actor_id = "user-456"
    record.session_id = None
    record.trace_id = None
    record.span_id = None
    record.action = "test.action"
    record.outcome = "success"
    for k, v in kwargs.items():
        setattr(record, k, v)
    return record


# ---------------------------------------------------------------------------
# Session ID Context Propagation
# ---------------------------------------------------------------------------

class SessionContextTests(unittest.TestCase):
    def test_bind_session_context_appears_in_enricher(self) -> None:
        enricher = ContextEnricher()
        record = _make_record()
        token = bind_session_context("sess-abc-123")
        try:
            enricher.filter(record)
            self.assertEqual(record.session_id, "sess-abc-123")
        finally:
            reset_session_context(token)

    def test_session_id_defaults_to_none(self) -> None:
        enricher = ContextEnricher()
        record = _make_record()
        enricher.filter(record)
        self.assertIsNone(record.session_id)

    def test_session_id_resets_correctly(self) -> None:
        enricher = ContextEnricher()
        token = bind_session_context("sess-1")
        reset_session_context(token)
        record = _make_record()
        enricher.filter(record)
        self.assertIsNone(record.session_id)


class SessionInJsonFormatterTests(unittest.TestCase):
    def test_json_formatter_includes_session_id(self) -> None:
        formatter = JsonFormatter()
        record = _make_record(session_id="sess-json-789")
        output = formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["session_id"], "sess-json-789")

    def test_json_formatter_session_id_none_still_present(self) -> None:
        formatter = JsonFormatter()
        record = _make_record(session_id=None)
        output = formatter.format(record)
        data = json.loads(output)
        # session_id should be in extra (even if None)
        self.assertIn("session_id", data)


class SessionInECSFormatterTests(unittest.TestCase):
    def test_ecs_formatter_includes_session_id(self) -> None:
        formatter = ECSFormatter()
        record = _make_record(session_id="sess-ecs-111")
        output = formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["session.id"], "sess-ecs-111")

    def test_ecs_formatter_omits_session_id_when_none(self) -> None:
        formatter = ECSFormatter()
        record = _make_record(session_id=None)
        output = formatter.format(record)
        data = json.loads(output)
        self.assertNotIn("session.id", data)


class SessionInCEFFormatterTests(unittest.TestCase):
    def test_cef_formatter_includes_session_id(self) -> None:
        formatter = CEFFormatter()
        record = _make_record(session_id="sess-cef-222")
        output = formatter.format(record)
        self.assertIn("cs5=sess-cef-222", output)
        self.assertIn("cs5Label=SessionID", output)

    def test_cef_formatter_omits_session_id_when_none(self) -> None:
        formatter = CEFFormatter()
        record = _make_record(session_id=None)
        output = formatter.format(record)
        self.assertNotIn("cs5=", output)
        self.assertNotIn("SessionID", output)


class SessionInSyslogFormatterTests(unittest.TestCase):
    def test_syslog_formatter_includes_session_id(self) -> None:
        formatter = SyslogFormatter()
        record = _make_record(session_id="sess-sys-333")
        output = formatter.format(record)
        self.assertIn('sessionId="sess-sys-333"', output)

    def test_syslog_formatter_omits_session_id_when_none(self) -> None:
        formatter = SyslogFormatter()
        record = _make_record(session_id=None)
        output = formatter.format(record)
        self.assertNotIn("sessionId=", output)


class SessionInTextFormatterTests(unittest.TestCase):
    def test_text_formatter_includes_session_id(self) -> None:
        formatter = TextFormatter()
        record = _make_record(session_id="sess-text-444-longvalue")
        output = formatter.format(record)
        self.assertIn("[sid:sess-tex]", output)

    def test_text_formatter_omits_session_id_when_empty(self) -> None:
        formatter = TextFormatter()
        record = _make_record(session_id=None)
        output = formatter.format(record)
        self.assertNotIn("[sid:", output)


# ---------------------------------------------------------------------------
# Route Template Resolution
# ---------------------------------------------------------------------------

class RouteTemplateMapTests(unittest.TestCase):
    def test_build_endpoint_route_map_extracts_routes(self) -> None:
        mock_app = MagicMock()
        route1 = MagicMock()
        route1.endpoint = lambda: None
        route1.path = "/api/v1/users/{user_id}"
        route2 = MagicMock()
        route2.endpoint = lambda: None
        route2.path = "/api/v1/health"
        mock_app.routes = [route1, route2]

        route_map = telemetry_module._build_endpoint_route_map(mock_app)
        self.assertEqual(route_map[id(route1.endpoint)], "/api/v1/users/{user_id}")
        self.assertEqual(route_map[id(route2.endpoint)], "/api/v1/health")

    def test_build_endpoint_route_map_handles_no_routes(self) -> None:
        mock_app = MagicMock()
        mock_app.routes = []
        route_map = telemetry_module._build_endpoint_route_map(mock_app)
        self.assertEqual(route_map, {})

    def test_build_endpoint_route_map_skips_routes_without_endpoint(self) -> None:
        mock_app = MagicMock()
        route = MagicMock(spec=[])  # No attributes
        mock_app.routes = [route]
        route_map = telemetry_module._build_endpoint_route_map(mock_app)
        self.assertEqual(route_map, {})


# ---------------------------------------------------------------------------
# Function Call Accumulator
# ---------------------------------------------------------------------------

class FunctionCallAccumulatorTests(unittest.TestCase):
    def test_increment_and_flush(self) -> None:
        mock_counter = MagicMock()
        acc = _FunctionCallAccumulator(mock_counter, flush_interval=9999)

        acc.increment("mod.a", "func_a", "ClassA.func_a", "backend/mod/a.py")
        acc.increment("mod.a", "func_a", "ClassA.func_a", "backend/mod/a.py")
        acc.increment("mod.b", "func_b", "func_b", "backend/mod/b.py")

        acc.flush()

        calls = mock_counter.add.call_args_list
        self.assertEqual(len(calls), 2)

        # Find the call for func_a
        func_a_calls = [c for c in calls if c[0][1]["code.function"] == "func_a"]
        self.assertEqual(len(func_a_calls), 1)
        self.assertEqual(func_a_calls[0][0][0], 2)  # count=2

        func_b_calls = [c for c in calls if c[0][1]["code.function"] == "func_b"]
        self.assertEqual(len(func_b_calls), 1)
        self.assertEqual(func_b_calls[0][0][0], 1)  # count=1

    def test_flush_clears_counts(self) -> None:
        mock_counter = MagicMock()
        acc = _FunctionCallAccumulator(mock_counter, flush_interval=9999)

        acc.increment("mod", "fn", "fn", "f.py")
        acc.flush()
        mock_counter.reset_mock()

        acc.flush()
        mock_counter.add.assert_not_called()

    def test_start_and_stop(self) -> None:
        mock_counter = MagicMock()
        acc = _FunctionCallAccumulator(mock_counter, flush_interval=9999)

        acc.start()
        self.assertTrue(acc._running)
        self.assertIsNotNone(acc._timer)

        acc.increment("mod", "fn", "fn", "f.py")
        acc.stop()

        self.assertFalse(acc._running)
        # Final flush should have been called
        mock_counter.add.assert_called_once()

    def test_thread_safety(self) -> None:
        mock_counter = MagicMock()
        acc = _FunctionCallAccumulator(mock_counter, flush_interval=9999)

        def worker(n: int) -> None:
            for _ in range(100):
                acc.increment("mod", f"fn_{n}", f"fn_{n}", "f.py")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        acc.flush()
        total = sum(call[0][0] for call in mock_counter.add.call_args_list)
        self.assertEqual(total, 400)

    def test_accumulator_attributes_match_otel_schema(self) -> None:
        mock_counter = MagicMock()
        acc = _FunctionCallAccumulator(mock_counter, flush_interval=9999)

        acc.increment("backend.auth", "login", "AuthService.login", "backend/03_auth_manage/service.py")
        acc.flush()

        attrs = mock_counter.add.call_args[0][1]
        self.assertEqual(attrs["code.module"], "backend.auth")
        self.assertEqual(attrs["code.function"], "login")
        self.assertEqual(attrs["code.qualified_name"], "AuthService.login")
        self.assertEqual(attrs["code.filepath"], "backend/03_auth_manage/service.py")


# ---------------------------------------------------------------------------
# Instrumentation Deduplication
# ---------------------------------------------------------------------------

class InstrumentationDedupTests(unittest.TestCase):
    def test_instrument_function_sets_marker(self) -> None:
        @telemetry_module.instrument_function(span_name="test.fn")
        def my_function():
            return 42

        # The marker should be on the original function (accessed via __wrapped__)
        original = getattr(my_function, "__wrapped__", my_function)
        self.assertTrue(getattr(original, _INSTRUMENTED_MARKER, False))

    def test_instrument_function_sync_still_works(self) -> None:
        @telemetry_module.instrument_function(span_name="test.sync")
        def add(a, b):
            return a + b

        result = add(3, 4)
        self.assertEqual(result, 7)

    def test_instrument_function_async_still_works(self) -> None:
        import asyncio

        @telemetry_module.instrument_function(span_name="test.async")
        async def async_add(a, b):
            return a + b

        result = asyncio.run(async_add(5, 6))
        self.assertEqual(result, 11)


# ---------------------------------------------------------------------------
# Settings for new fields
# ---------------------------------------------------------------------------

class NewSettingsFieldsTests(unittest.TestCase):
    def test_function_metrics_defaults(self) -> None:
        settings = _make_settings()
        self.assertFalse(settings.otel_function_metrics_enabled)
        self.assertEqual(settings.otel_function_metrics_flush_interval_seconds, 15)

    def test_function_metrics_custom_values(self) -> None:
        settings = _make_settings(
            otel_function_metrics_enabled=True,
            otel_function_metrics_flush_interval_seconds=30,
        )
        self.assertTrue(settings.otel_function_metrics_enabled)
        self.assertEqual(settings.otel_function_metrics_flush_interval_seconds, 30)

    def test_glitchtip_defaults(self) -> None:
        settings = _make_settings()
        self.assertIsNone(settings.glitchtip_dsn)
        self.assertAlmostEqual(settings.glitchtip_traces_sample_rate, 0.1)

    def test_glitchtip_custom_dsn(self) -> None:
        settings = _make_settings(
            glitchtip_dsn="https://key@glitchtip.example.com/1",
            glitchtip_traces_sample_rate=0.5,
        )
        self.assertEqual(settings.glitchtip_dsn, "https://key@glitchtip.example.com/1")
        self.assertAlmostEqual(settings.glitchtip_traces_sample_rate, 0.5)


# ---------------------------------------------------------------------------
# GlitchTip Integration
# ---------------------------------------------------------------------------

class GlitchTipConfigTests(unittest.TestCase):
    def test_configure_glitchtip_skips_when_no_dsn(self) -> None:
        settings = _make_settings(glitchtip_dsn=None)
        # Should not raise
        telemetry_module._configure_glitchtip(settings)

    def test_configure_glitchtip_logs_warning_when_sdk_missing(self) -> None:
        settings = _make_settings(glitchtip_dsn="https://key@glitchtip.example.com/1")
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            # Should not raise, just log warning
            telemetry_module._configure_glitchtip(settings)


# ---------------------------------------------------------------------------
# Shutdown with accumulator
# ---------------------------------------------------------------------------

class ShutdownWithAccumulatorTests(unittest.TestCase):
    def test_shutdown_stops_accumulator(self) -> None:
        mock_acc = MagicMock()
        mock_acc.stop = MagicMock()

        with (
            patch.object(telemetry_module, "_tracer_provider", None),
            patch.object(telemetry_module, "_logger_provider", None),
            patch.object(telemetry_module, "_meter_provider", None),
            patch.object(telemetry_module, "_function_call_accumulator", mock_acc),
        ):
            telemetry_module.shutdown_observability()

        mock_acc.stop.assert_called_once()

    def test_shutdown_handles_none_accumulator(self) -> None:
        with (
            patch.object(telemetry_module, "_tracer_provider", None),
            patch.object(telemetry_module, "_logger_provider", None),
            patch.object(telemetry_module, "_meter_provider", None),
            patch.object(telemetry_module, "_function_call_accumulator", None),
        ):
            telemetry_module.shutdown_observability()
