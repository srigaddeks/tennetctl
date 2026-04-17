"""FastAPI middleware — emit server-kind spans + latency histograms.

Every inbound request (except skipped paths) creates an OTel Span protobuf
and publishes it to JetStream subject ``monitoring.traces.otel.tennetctl-backend``.
Also records histogram + counter metrics (in-memory stubs for now; Plan 13-02
owns the real metrics pipe — we publish spans and keep metrics as hook points
the 13-02 SDK can wrap).

Trace context: reads W3C ``traceparent`` header if present (propagates
trace_id), otherwise generates a new 128-bit trace_id.

Skips: ``/v1/monitoring/otlp/``, ``/health``, ``/docs``, ``/openapi.json``,
``/redoc``.
"""

from __future__ import annotations

import logging
import os
import time
from importlib import import_module
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from opentelemetry.proto.trace.v1.trace_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ResourceSpans,
    ScopeSpans,
    Span,
)
from opentelemetry.proto.common.v1.common_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    AnyValue,
    InstrumentationScope,
    KeyValue,
)
from opentelemetry.proto.resource.v1.resource_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    Resource,
)

from . import _in_monitoring_bridge

logger = logging.getLogger("tennetctl.monitoring.instrumentation.fastapi")

_SKIP_PREFIXES = (
    "/v1/monitoring/otlp/",
    "/v1/monitoring/logs/tail",  # SSE — BaseHTTPMiddleware buffers streams
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)
_SELF_SUBJECT = "monitoring.traces.otel.tennetctl-backend"


def _should_skip(path: str) -> bool:
    for pref in _SKIP_PREFIXES:
        if path.startswith(pref):
            return True
    return False


def _parse_traceparent(tp: str | None) -> tuple[bytes, bytes] | None:
    """Parse W3C traceparent. Returns (trace_id_bytes, parent_span_id_bytes) or None."""
    if not tp:
        return None
    parts = tp.split("-")
    if len(parts) != 4:
        return None
    try:
        trace_id = bytes.fromhex(parts[1])
        span_id = bytes.fromhex(parts[2])
        if len(trace_id) != 16 or len(span_id) != 8:
            return None
        return trace_id, span_id
    except ValueError:
        return None


def _new_trace_id() -> bytes:
    return os.urandom(16)


def _new_span_id() -> bytes:
    return os.urandom(8)


def _kv_str(key: str, value: str) -> KeyValue:
    return KeyValue(key=key, value=AnyValue(string_value=value))


def _kv_int(key: str, value: int) -> KeyValue:
    return KeyValue(key=key, value=AnyValue(int_value=value))


def _build_span_proto(
    method: str,
    route: str,
    target: str,
    status_code: int,
    trace_id: bytes,
    span_id: bytes,
    parent_span_id: bytes,
    start_ns: int,
    end_ns: int,
) -> bytes:
    span = Span(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        name=f"{method} {route}",
        kind=Span.SPAN_KIND_SERVER,
        start_time_unix_nano=start_ns,
        end_time_unix_nano=end_ns,
    )
    span.attributes.extend([
        _kv_str("http.method", method),
        _kv_str("http.route", route),
        _kv_str("http.target", target),
        _kv_int("http.status_code", status_code),
    ])
    resource = Resource()
    resource.attributes.append(_kv_str("service.name", "tennetctl-backend"))

    rs = ResourceSpans(resource=resource)
    ss = ScopeSpans(scope=InstrumentationScope(name="tennetctl.fastapi"))
    ss.spans.append(span)
    rs.scope_spans.append(ss)
    return rs.SerializeToString()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Emit a server-kind span per request. Skips infra paths."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        path = request.url.path
        if _should_skip(path):
            return await call_next(request)

        # Reentrancy guard — if we're already inside a monitoring publish,
        # skip span emission to prevent loops.
        guarded = _in_monitoring_bridge.get()

        tp = _parse_traceparent(request.headers.get("traceparent"))
        if tp is not None:
            trace_id, parent_span_id = tp
        else:
            trace_id = _new_trace_id()
            parent_span_id = b"\x00" * 8

        span_id = _new_span_id()
        start_ns = time.time_ns()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            end_ns = time.time_ns()
            if not guarded:
                token = _in_monitoring_bridge.set(True)
                try:
                    await _publish_span(
                        method=request.method,
                        route=getattr(request.scope.get("route"), "path", None) or path,
                        target=str(request.url.path),
                        status_code=status_code,
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        start_ns=start_ns,
                        end_ns=end_ns,
                    )
                finally:
                    _in_monitoring_bridge.reset(token)


async def _publish_span(**kwargs: Any) -> None:
    """Publish a span to JetStream. Silent-drop on failure."""
    _nats_core: Any = import_module("backend.01_core.nats")
    try:
        js = _nats_core.get_js()
    except RuntimeError:
        return  # NATS not connected
    try:
        payload = _build_span_proto(**kwargs)
        await js.publish(_SELF_SUBJECT, payload)
    except Exception as e:  # noqa: BLE001
        logger.debug("monitoring fastapi span publish failed: %s", e)


def install(app: Any, config: Any) -> None:
    """Register the middleware on the FastAPI app (last — measures everything)."""
    del config  # reserved for future config gating
    app.add_middleware(MonitoringMiddleware)
