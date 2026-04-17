"""Stdlib logging → OTLP LogRecord bridge.

Installs a ``logging.Handler`` on the root logger that publishes every log
record to JetStream subject ``monitoring.logs.otel.tennetctl-backend``. Uses
a ContextVar reentrancy guard to prevent infinite loops (publish emits its
own logs, etc.).

``install()`` is idempotent.
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

from opentelemetry.proto.logs.v1.logs_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    LogRecord,
    ResourceLogs,
    ScopeLogs,
    SeverityNumber,
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

_SELF_SUBJECT = "monitoring.logs.otel.tennetctl-backend"
_INSTALLED = False
_DROP_COUNT = 0  # simple in-proc counter for monitoring.bridge.drops_total

_LEVEL_TO_OTEL_SEV = {
    logging.DEBUG: SeverityNumber.SEVERITY_NUMBER_DEBUG,
    logging.INFO: SeverityNumber.SEVERITY_NUMBER_INFO,
    logging.WARNING: SeverityNumber.SEVERITY_NUMBER_WARN,
    logging.ERROR: SeverityNumber.SEVERITY_NUMBER_ERROR,
    logging.CRITICAL: SeverityNumber.SEVERITY_NUMBER_FATAL,
}


def get_drop_count() -> int:
    """Return the current in-proc drop counter (for tests/introspection)."""
    return _DROP_COUNT


def _build_log_payload(record: logging.LogRecord) -> bytes:
    sev = _LEVEL_TO_OTEL_SEV.get(
        record.levelno, SeverityNumber.SEVERITY_NUMBER_UNSPECIFIED
    )
    lr = LogRecord(
        time_unix_nano=int(record.created * 1e9),
        severity_number=sev,
        severity_text=record.levelname,
        body=AnyValue(string_value=record.getMessage()),
    )
    lr.attributes.append(
        KeyValue(key="logger.name", value=AnyValue(string_value=record.name))
    )
    resource = Resource()
    resource.attributes.append(
        KeyValue(key="service.name", value=AnyValue(string_value="tennetctl-backend"))
    )
    rl = ResourceLogs(resource=resource)
    sl = ScopeLogs(scope=InstrumentationScope(name="tennetctl.logging"))
    sl.log_records.append(lr)
    rl.scope_logs.append(sl)
    return rl.SerializeToString()


async def _publish(payload: bytes) -> None:
    global _DROP_COUNT
    _nats_core: Any = import_module("backend.01_core.nats")
    try:
        js = _nats_core.get_js()
    except RuntimeError:
        _DROP_COUNT += 1
        return
    try:
        await js.publish(_SELF_SUBJECT, payload)
    except Exception:  # noqa: BLE001
        _DROP_COUNT += 1


class MonitoringLogHandler(logging.Handler):
    """Bridge stdlib log records to JetStream via OTLP LogRecord protobuf."""

    def emit(self, record: logging.LogRecord) -> None:
        global _DROP_COUNT
        # Guard: don't recurse.
        if _in_monitoring_bridge.get():
            return
        # Only forward application-namespace logs (tennetctl.*). Avoids
        # forwarding uvicorn / asyncpg / third-party log spam.
        if not record.name.startswith("tennetctl"):
            return
        # Skip our own instrumentation loggers to avoid chatter.
        if record.name.startswith("tennetctl.monitoring.instrumentation"):
            return
        if record.name.startswith("tennetctl.monitoring.logs"):
            return
        if record.name.startswith("tennetctl.monitoring.traces"):
            return
        try:
            payload = _build_log_payload(record)
        except Exception:  # noqa: BLE001
            _DROP_COUNT += 1
            return

        token = _in_monitoring_bridge.set(True)
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_guarded_publish(payload, token))
                    return  # token consumed by task
                else:
                    loop.run_until_complete(_publish(payload))
            except RuntimeError:
                _DROP_COUNT += 1
        finally:
            # If we didn't schedule a task, reset now. If we did, task resets.
            try:
                _in_monitoring_bridge.reset(token)
            except (LookupError, ValueError):
                pass


async def _guarded_publish(payload: bytes, token: Any) -> None:
    try:
        await _publish(payload)
    finally:
        try:
            _in_monitoring_bridge.reset(token)
        except (LookupError, ValueError):
            pass


def install() -> None:
    """Add the bridge handler to the root logger. Idempotent."""
    global _INSTALLED
    if _INSTALLED:
        return
    handler = MonitoringLogHandler(level=logging.INFO)
    logging.getLogger().addHandler(handler)
    _INSTALLED = True


def _reset_for_tests() -> None:
    """Remove handler + reset flags. Tests only."""
    global _INSTALLED, _DROP_COUNT
    root = logging.getLogger()
    for h in list(root.handlers):
        if isinstance(h, MonitoringLogHandler):
            root.removeHandler(h)
    _INSTALLED = False
    _DROP_COUNT = 0


__all__ = [
    "MonitoringLogHandler",
    "install",
    "get_drop_count",
    "_reset_for_tests",
]
