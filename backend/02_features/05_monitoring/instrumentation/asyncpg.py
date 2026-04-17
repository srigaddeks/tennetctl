"""asyncpg query instrumentation.

Wraps the pool's connect setup so every new connection gets a query logger
that emits a client-kind span per query. SQL statement literals are redacted
with a regex and truncated to 256 chars before ending up on the wire.
"""

from __future__ import annotations

import logging
import os
import re
import time
from importlib import import_module
from typing import Any

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

logger = logging.getLogger("tennetctl.monitoring.instrumentation.asyncpg")

_SELF_SUBJECT = "monitoring.traces.otel.tennetctl-backend"
_MAX_STATEMENT = 256

# Redact string literals ('...') and numeric literals.
_STRING_LITERAL_RE = re.compile(r"'([^']|'')*'")
_NUMERIC_LITERAL_RE = re.compile(r"\b\d+(\.\d+)?\b")


def redact_sql(stmt: str) -> str:
    """Replace string and numeric literals with ``?`` and truncate."""
    if not stmt:
        return ""
    s = _STRING_LITERAL_RE.sub("?", stmt)
    s = _NUMERIC_LITERAL_RE.sub("?", s)
    if len(s) > _MAX_STATEMENT:
        s = s[:_MAX_STATEMENT]
    return s


def _kv_str(key: str, value: str) -> KeyValue:
    return KeyValue(key=key, value=AnyValue(string_value=value))


def _kv_int(key: str, value: int) -> KeyValue:
    return KeyValue(key=key, value=AnyValue(int_value=value))


def _build_query_span(
    statement: str,
    duration_ns: int,
    end_ns: int,
) -> bytes:
    span = Span(
        trace_id=os.urandom(16),
        span_id=os.urandom(8),
        parent_span_id=b"\x00" * 8,
        name="pg.query",
        kind=Span.SPAN_KIND_CLIENT,
        start_time_unix_nano=end_ns - duration_ns,
        end_time_unix_nano=end_ns,
    )
    span.attributes.extend([
        _kv_str("db.system", "postgresql"),
        _kv_str("db.statement", redact_sql(statement)),
    ])
    resource = Resource()
    resource.attributes.append(_kv_str("service.name", "tennetctl-backend"))

    rs = ResourceSpans(resource=resource)
    ss = ScopeSpans(scope=InstrumentationScope(name="tennetctl.asyncpg"))
    ss.spans.append(span)
    rs.scope_spans.append(ss)
    return rs.SerializeToString()


async def _publish_query_span(statement: str, duration_ns: int, end_ns: int) -> None:
    _nats_core: Any = import_module("backend.01_core.nats")
    try:
        js = _nats_core.get_js()
    except RuntimeError:
        return
    try:
        payload = _build_query_span(statement, duration_ns, end_ns)
        await js.publish(_SELF_SUBJECT, payload)
    except Exception as e:  # noqa: BLE001
        logger.debug("monitoring asyncpg span publish failed: %s", e)


def make_query_logger() -> Any:
    """Return an asyncpg query-logger callback.

    asyncpg's `conn.add_query_logger` invokes with a `LoggedQuery`-like record
    that has ``.query``, ``.elapsed`` (seconds float) fields.
    """

    def _callback(record: Any) -> None:
        if _in_monitoring_bridge.get():
            return
        stmt = getattr(record, "query", "") or ""
        elapsed = getattr(record, "elapsed", 0.0) or 0.0
        duration_ns = int(elapsed * 1e9)
        end_ns = time.time_ns()
        # Schedule publish via running loop; we're inside asyncpg's callback
        # which may be sync. Use ensure_future.
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            token = _in_monitoring_bridge.set(True)

            async def _run():
                try:
                    await _publish_query_span(stmt, duration_ns, end_ns)
                finally:
                    _in_monitoring_bridge.reset(token)

            loop.create_task(_run())
        except RuntimeError:
            # No running loop — silent drop.
            pass

    return _callback


async def _attach_to_conn(conn: Any) -> None:
    """Register the query logger on a freshly acquired connection."""
    try:
        conn.add_query_logger(make_query_logger())
    except Exception as e:  # noqa: BLE001
        logger.debug("monitoring asyncpg add_query_logger failed: %s", e)


def install(pool: Any) -> None:
    """Attach query loggers to all current + future pool connections.

    asyncpg.Pool exposes internal ``_holders`` — we walk current holders and
    attach; new connections get attached via a post-init hook.
    """
    if pool is None:
        return
    # Attach to existing holders (best-effort).
    holders = getattr(pool, "_holders", None) or []
    for holder in holders:
        conn = getattr(holder, "_con", None)
        if conn is not None:
            try:
                conn.add_query_logger(make_query_logger())
            except Exception:  # noqa: BLE001
                pass

    # Wrap pool._async__init__ or .acquire to attach on each new connection.
    # The safest portable seam: monkey-patch pool.acquire to attach once per conn.
    original_acquire = pool.acquire

    _attached: set[int] = set()

    async def _wrapped_acquire(*args: Any, **kwargs: Any) -> Any:
        conn = await original_acquire(*args, **kwargs)
        cid = id(conn)
        if cid not in _attached:
            _attached.add(cid)
            try:
                conn.add_query_logger(make_query_logger())
            except Exception:  # noqa: BLE001
                pass
        return conn

    # pool.acquire returns an async context manager; above wraps the coroutine
    # form. Keep attribute for manual acquisitions. Do NOT break the ctx form.
    try:
        pool.acquire = _wrapped_acquire  # type: ignore[assignment]
    except Exception:  # noqa: BLE001
        pass


__all__ = ["install", "redact_sql", "make_query_logger"]
