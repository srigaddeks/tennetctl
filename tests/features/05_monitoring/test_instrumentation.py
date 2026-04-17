"""Tests for FastAPI + asyncpg + structlog bridge instrumentation."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

_instr: Any = import_module("backend.02_features.05_monitoring.instrumentation")
_fastapi_mod: Any = import_module(
    "backend.02_features.05_monitoring.instrumentation.fastapi"
)
_asyncpg_mod: Any = import_module(
    "backend.02_features.05_monitoring.instrumentation.asyncpg"
)
_bridge: Any = import_module(
    "backend.02_features.05_monitoring.instrumentation.structlog_bridge"
)
_nats_core: Any = import_module("backend.01_core.nats")


@pytest.fixture(autouse=True)
def _reset_bridge():
    _bridge._reset_for_tests()
    yield
    _bridge._reset_for_tests()


def _fake_js():
    js = MagicMock()
    js.publish = AsyncMock()
    return js


async def test_fastapi_middleware_emits_span():
    app = FastAPI()

    @app.get("/widget")
    async def widget():
        return {"ok": True}

    _fastapi_mod.install(app, None)
    js = _fake_js()
    with patch.object(_nats_core, "get_js", return_value=js):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/widget")
            assert r.status_code == 200

    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.traces.otel.tennetctl-backend"
    assert isinstance(args[1], bytes) and len(args[1]) > 0


async def test_fastapi_middleware_skips_infra_paths():
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"ok": True}

    _fastapi_mod.install(app, None)
    js = _fake_js()
    with patch.object(_nats_core, "get_js", return_value=js):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/health")

    js.publish.assert_not_awaited()


async def test_fastapi_middleware_propagates_traceparent():
    app = FastAPI()

    @app.get("/x")
    async def x():
        return {"ok": True}

    _fastapi_mod.install(app, None)
    js = _fake_js()
    trace_hex = "0af7651916cd43dd8448eb211c80319c"
    parent_span_hex = "b7ad6b7169203331"
    header = f"00-{trace_hex}-{parent_span_hex}-01"
    with patch.object(_nats_core, "get_js", return_value=js):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/x", headers={"traceparent": header})

    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    # Decode the published ResourceSpans and verify trace_id
    from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans  # type: ignore
    rs = ResourceSpans()
    rs.ParseFromString(args[1])
    span = rs.scope_spans[0].spans[0]
    assert span.trace_id.hex() == trace_hex
    assert span.parent_span_id.hex() == parent_span_hex


def test_asyncpg_redact_sql_replaces_literals():
    stmt = "SELECT * FROM users WHERE email='x@y.z' AND age=42"
    redacted = _asyncpg_mod.redact_sql(stmt)
    assert "x@y.z" not in redacted
    assert "42" not in redacted
    assert "?" in redacted


def test_asyncpg_redact_sql_truncates_to_256():
    stmt = "SELECT " + ("a, " * 200) + "FROM t"
    redacted = _asyncpg_mod.redact_sql(stmt)
    assert len(redacted) <= 256


async def test_asyncpg_query_logger_publishes_span():
    js = _fake_js()
    import asyncio

    class FakeRecord:
        query = "SELECT 1"
        elapsed = 0.001

    with patch.object(_nats_core, "get_js", return_value=js):
        cb = _asyncpg_mod.make_query_logger()
        cb(FakeRecord())
        # callback schedules a create_task — give it one loop iteration
        await asyncio.sleep(0.05)

    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.traces.otel.tennetctl-backend"


async def test_structlog_bridge_publishes_info_log():
    js = _fake_js()
    with patch.object(_nats_core, "get_js", return_value=js):
        _bridge.install()
        log = logging.getLogger("tennetctl.tests.bridge")
        log.setLevel(logging.INFO)
        log.info("hello-from-test")
        # Let the scheduled task run
        import asyncio
        await asyncio.sleep(0.05)

    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.logs.otel.tennetctl-backend"


async def test_structlog_bridge_silent_drop_on_nats_down():
    # get_js raises RuntimeError when NATS not connected — bridge must not crash
    def _raise():
        raise RuntimeError("NATS not connected")

    with patch.object(_nats_core, "get_js", side_effect=_raise):
        _bridge.install()
        drops_before = _bridge.get_drop_count()
        log = logging.getLogger("tennetctl.tests.bridge.down")
        log.setLevel(logging.INFO)
        log.info("this-should-silent-drop")
        import asyncio
        await asyncio.sleep(0.05)

    # drop counter should have incremented
    assert _bridge.get_drop_count() > drops_before


async def test_structlog_bridge_recursion_guard():
    """Log emitted from inside the bridge's publish path must not loop."""
    js = _fake_js()

    # Second invocation simulates a log originating from inside publish.
    with patch.object(_nats_core, "get_js", return_value=js):
        _bridge.install()
        token = _instr._in_monitoring_bridge.set(True)
        try:
            log = logging.getLogger("tennetctl.tests.bridge.guard")
            log.setLevel(logging.INFO)
            log.info("should-be-suppressed")
            import asyncio
            await asyncio.sleep(0.05)
        finally:
            _instr._in_monitoring_bridge.reset(token)

    # No publish because guard short-circuited emit()
    js.publish.assert_not_awaited()
