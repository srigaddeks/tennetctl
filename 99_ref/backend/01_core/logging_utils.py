from __future__ import annotations

from contextvars import ContextVar, Token
from datetime import UTC, datetime
import json
import logging
import socket


try:
    from opentelemetry import trace as otel_trace
except ImportError:  # pragma: no cover
    otel_trace = None


_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_ACTOR_ID: ContextVar[str | None] = ContextVar("actor_id", default=None)
_SESSION_ID: ContextVar[str | None] = ContextVar("session_id", default=None)
_IMPERSONATOR_ID: ContextVar[str | None] = ContextVar("impersonator_id", default=None)
_LOGGING_STATE: dict[str, str | None] = {"service": None, "environment": None}
_BASE_RECORD_FACTORY = logging.getLogRecordFactory()
_FACTORY_CONFIGURED = False

SUPPORTED_LOG_FORMATS = frozenset({"json", "text", "ecs", "cef", "syslog"})


def bind_request_context(request_id: str | None) -> Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_context(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


def bind_actor_context(actor_id: str | None) -> Token[str | None]:
    return _ACTOR_ID.set(actor_id)


def reset_actor_context(token: Token[str | None]) -> None:
    _ACTOR_ID.reset(token)


def bind_session_context(session_id: str | None) -> Token[str | None]:
    return _SESSION_ID.set(session_id)


def reset_session_context(token: Token[str | None]) -> None:
    _SESSION_ID.reset(token)


def bind_impersonator_context(impersonator_id: str | None) -> Token[str | None]:
    return _IMPERSONATOR_ID.set(impersonator_id)


def reset_impersonator_context(token: Token[str | None]) -> None:
    _IMPERSONATOR_ID.reset(token)


class ContextEnricher(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.service = _LOGGING_STATE["service"]
        record.environment = _LOGGING_STATE["environment"]
        record.request_id = _REQUEST_ID.get()
        record.actor_id = _ACTOR_ID.get()
        record.session_id = _SESSION_ID.get()
        record.impersonator_id = _IMPERSONATOR_ID.get()
        record.action = getattr(record, "action", record.getMessage())
        record.outcome = getattr(record, "outcome", "unknown")
        record.trace_id = None
        record.span_id = None
        if otel_trace is not None:
            span = otel_trace.get_current_span()
            span_context = span.get_span_context() if span is not None else None
            if span_context is not None and span_context.is_valid:
                record.trace_id = format(span_context.trace_id, "032x")
                record.span_id = format(span_context.span_id, "016x")
        return True


def _record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _BASE_RECORD_FACTORY(*args, **kwargs)
    record.trace_id = getattr(record, "trace_id", None)
    record.span_id = getattr(record, "span_id", None)
    if otel_trace is not None:
        span = otel_trace.get_current_span()
        span_context = span.get_span_context() if span is not None else None
        if span_context is not None and span_context.is_valid:
            record.trace_id = format(span_context.trace_id, "032x")
            record.span_id = format(span_context.span_id, "016x")
    return record


# ---------------------------------------------------------------------------
# Sensitive field redaction
# ---------------------------------------------------------------------------

_SENSITIVE_LOG_KEYS = frozenset({
    "password", "secret", "token", "authorization", "cookie",
    "api_key", "apikey", "credential", "access_token", "refresh_token",
})


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact_value(v) if _is_sensitive_log_key(k) else _redact_dict_values(v) for k, v in value.items()}
    return "[REDACTED]"


def _is_sensitive_log_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _SENSITIVE_LOG_KEYS)


def _redact_dict_values(value: object) -> object:
    if isinstance(value, dict):
        return {k: _redact_value(v) if _is_sensitive_log_key(k) else _redact_dict_values(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# Common record → dict extraction (shared by JSON, ECS, CEF formatters)
# ---------------------------------------------------------------------------

_EXCLUDED_RECORD_KEYS = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "module", "msecs", "message",
    "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName",
    "taskName",
})


def _extract_extra(record: logging.LogRecord) -> dict[str, object]:
    extra: dict[str, object] = {}
    for key, value in record.__dict__.items():
        if key.startswith("_") or key in _EXCLUDED_RECORD_KEYS:
            continue
        if _is_sensitive_log_key(key):
            extra[key] = "[REDACTED]"
        else:
            extra[key] = _redact_dict_values(value)
    return extra


def _format_exception_dict(record: logging.LogRecord, formatter: logging.Formatter) -> dict[str, str] | None:
    if not record.exc_info or record.exc_info[1] is None:
        return None
    return {
        "type": type(record.exc_info[1]).__name__,
        "message": str(record.exc_info[1]),
        "traceback": formatter.formatException(record.exc_info),
    }


# ---------------------------------------------------------------------------
# Formatter: JSON (default, works with Datadog, Loki, CloudWatch, etc.)
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_extract_extra(record))
        exc = _format_exception_dict(record, self)
        if exc:
            payload["exception"] = exc
        return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# Formatter: ECS (Elastic Common Schema — for Elasticsearch / Elastic SIEM)
# https://www.elastic.co/guide/en/ecs/current/ecs-reference.html
# ---------------------------------------------------------------------------

_ECS_LOG_LEVEL_MAP = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warn",
    "ERROR": "error",
    "CRITICAL": "critical",
}


class ECSFormatter(logging.Formatter):
    """Elastic Common Schema v8 JSON formatter."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(tz=UTC).isoformat()
        ecs: dict[str, object] = {
            "@timestamp": timestamp,
            "log.level": _ECS_LOG_LEVEL_MAP.get(record.levelname, record.levelname.lower()),
            "log.logger": record.name,
            "message": record.getMessage(),
            "ecs.version": "8.11.0",
        }
        service = getattr(record, "service", None)
        environment = getattr(record, "environment", None)
        if service:
            ecs["service.name"] = service
        if environment:
            ecs["service.environment"] = environment

        request_id = getattr(record, "request_id", None)
        actor_id = getattr(record, "actor_id", None)
        session_id = getattr(record, "session_id", None)
        trace_id = getattr(record, "trace_id", None)
        span_id = getattr(record, "span_id", None)
        if trace_id:
            ecs["trace.id"] = trace_id
        if span_id:
            ecs["span.id"] = span_id
        if request_id:
            ecs["http.request.id"] = request_id
        if actor_id:
            ecs["user.id"] = actor_id
        if session_id:
            ecs["session.id"] = session_id
        impersonator_id = getattr(record, "impersonator_id", None)
        if impersonator_id:
            ecs["user.impersonator_id"] = impersonator_id

        exc = _format_exception_dict(record, self)
        if exc:
            ecs["error.type"] = exc["type"]
            ecs["error.message"] = exc["message"]
            ecs["error.stack_trace"] = exc["traceback"]

        # Remaining extra fields under "labels"
        extra = _extract_extra(record)
        labels: dict[str, object] = {}
        for key in ("service", "environment", "request_id", "actor_id", "session_id", "impersonator_id", "trace_id", "span_id", "action", "outcome"):
            extra.pop(key, None)
        if extra:
            labels.update(extra)
        if labels:
            ecs["labels"] = labels

        return json.dumps(ecs, default=str)


# ---------------------------------------------------------------------------
# Formatter: CEF (Common Event Format — for Splunk, ArcSight, QRadar)
# CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
# ---------------------------------------------------------------------------

_CEF_SEVERITY_MAP = {
    "DEBUG": 1,
    "INFO": 3,
    "WARNING": 5,
    "ERROR": 7,
    "CRITICAL": 10,
}


def _cef_escape(value: str) -> str:
    """Escape characters that are special in CEF extension values."""
    return value.replace("\\", "\\\\").replace("=", "\\=").replace("\n", "\\n").replace("\r", "\\r")


class CEFFormatter(logging.Formatter):
    """ArcSight Common Event Format formatter."""

    def __init__(self, vendor: str = "Kreesalis", product: str = "kcontrol", version: str = "1.0") -> None:
        super().__init__()
        self._vendor = vendor
        self._product = product
        self._version = version

    def format(self, record: logging.LogRecord) -> str:
        severity = _CEF_SEVERITY_MAP.get(record.levelname, 3)
        action = getattr(record, "action", record.getMessage()) or ""
        sig_id = action if isinstance(action, str) else str(action)
        message = record.getMessage()

        extensions: list[str] = []
        extensions.append(f"msg={_cef_escape(message)}")
        extensions.append(f"rt={datetime.now(tz=UTC).strftime('%b %d %Y %H:%M:%S')}")

        request_id = getattr(record, "request_id", None)
        actor_id = getattr(record, "actor_id", None)
        session_id = getattr(record, "session_id", None)
        trace_id = getattr(record, "trace_id", None)
        outcome = getattr(record, "outcome", None)

        if request_id:
            extensions.append(f"cs1={_cef_escape(request_id)}")
            extensions.append("cs1Label=RequestID")
        if actor_id:
            extensions.append(f"duser={_cef_escape(actor_id)}")
        if session_id:
            extensions.append(f"cs5={_cef_escape(session_id)}")
            extensions.append("cs5Label=SessionID")
        if trace_id:
            extensions.append(f"cs2={_cef_escape(trace_id)}")
            extensions.append("cs2Label=TraceID")
        if outcome:
            extensions.append(f"outcome={_cef_escape(str(outcome))}")
        impersonator_id = getattr(record, "impersonator_id", None)
        if impersonator_id:
            extensions.append(f"cs6={_cef_escape(impersonator_id)}")
            extensions.append("cs6Label=ImpersonatorID")

        exc = _format_exception_dict(record, self)
        if exc:
            extensions.append(f"cs3={_cef_escape(exc['type'])}")
            extensions.append("cs3Label=ExceptionType")
            extensions.append(f"cs4={_cef_escape(exc['message'][:1024])}")
            extensions.append("cs4Label=ExceptionMessage")

        ext_str = " ".join(extensions)
        header = f"CEF:0|{self._vendor}|{self._product}|{self._version}|{_cef_escape(sig_id)}|{_cef_escape(message[:512])}|{severity}"
        return f"{header}|{ext_str}"


# ---------------------------------------------------------------------------
# Formatter: Syslog (RFC 5424 structured data — for rsyslog, syslog-ng, Graylog)
# <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD-ID SD-PARAMS] MSG
# ---------------------------------------------------------------------------

_SYSLOG_SEVERITY_MAP = {
    "DEBUG": 7,
    "INFO": 6,
    "WARNING": 4,
    "ERROR": 3,
    "CRITICAL": 2,
}


def _sd_escape(value: str) -> str:
    """Escape characters per RFC 5424 structured data."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("]", "\\]")


class SyslogFormatter(logging.Formatter):
    """RFC 5424 syslog formatter with structured data."""

    def __init__(self, app_name: str = "kcontrol") -> None:
        super().__init__()
        self._app_name = app_name
        self._hostname = socket.gethostname()

    def format(self, record: logging.LogRecord) -> str:
        severity = _SYSLOG_SEVERITY_MAP.get(record.levelname, 6)
        facility = 1  # user-level
        pri = facility * 8 + severity
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        proc_id = str(record.process or "-")
        msg_id = getattr(record, "action", "-") or "-"
        if not isinstance(msg_id, str):
            msg_id = str(msg_id)

        sd_params: list[str] = []
        request_id = getattr(record, "request_id", None)
        actor_id = getattr(record, "actor_id", None)
        session_id = getattr(record, "session_id", None)
        trace_id = getattr(record, "trace_id", None)
        span_id = getattr(record, "span_id", None)
        outcome = getattr(record, "outcome", None)
        environment = getattr(record, "environment", None)

        if request_id:
            sd_params.append(f'requestId="{_sd_escape(request_id)}"')
        if actor_id:
            sd_params.append(f'actorId="{_sd_escape(actor_id)}"')
        if session_id:
            sd_params.append(f'sessionId="{_sd_escape(session_id)}"')
        if trace_id:
            sd_params.append(f'traceId="{_sd_escape(trace_id)}"')
        if span_id:
            sd_params.append(f'spanId="{_sd_escape(span_id)}"')
        if outcome:
            sd_params.append(f'outcome="{_sd_escape(str(outcome))}"')
        if environment:
            sd_params.append(f'env="{_sd_escape(str(environment))}"')
        impersonator_id = getattr(record, "impersonator_id", None)
        if impersonator_id:
            sd_params.append(f'impersonatorId="{_sd_escape(impersonator_id)}"')

        sd = f'[kcontrol@49610 {" ".join(sd_params)}]' if sd_params else "-"
        message = record.getMessage()

        exc = _format_exception_dict(record, self)
        if exc:
            message += f" | exception={exc['type']}: {exc['message']}"

        return f"<{pri}>1 {timestamp} {self._hostname} {self._app_name} {proc_id} {msg_id} {sd} {message}"


# ---------------------------------------------------------------------------
# Formatter: Text (human-readable for local development)
# ---------------------------------------------------------------------------

_LEVEL_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}
_RESET = "\033[0m"


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        color = _LEVEL_COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:<8}{_RESET}" if color else f"{record.levelname:<8}"
        service = getattr(record, "service", None) or ""
        request_id = getattr(record, "request_id", None) or ""
        actor_id = getattr(record, "actor_id", None) or ""
        session_id = getattr(record, "session_id", None) or ""

        parts = [f"[{timestamp}]", level]
        if service:
            parts.append(f"[{service}]")
        if request_id:
            parts.append(f"[req:{request_id[:8]}]")
        if actor_id:
            parts.append(f"[actor:{actor_id[:8]}]")
        if session_id:
            parts.append(f"[sid:{session_id[:8]}]")
        impersonator_id = getattr(record, "impersonator_id", None) or ""
        if impersonator_id:
            parts.append(f"[imp:{impersonator_id[:8]}]")
        parts.append(record.getMessage())

        line = " ".join(parts)
        if record.exc_info and record.exc_info[1] is not None:
            line += "\n" + self.formatException(record.exc_info)
        return line


# ---------------------------------------------------------------------------
# Formatter registry
# ---------------------------------------------------------------------------

_FORMATTER_REGISTRY: dict[str, type[logging.Formatter]] = {
    "json": JsonFormatter,
    "text": TextFormatter,
    "ecs": ECSFormatter,
    "cef": CEFFormatter,
    "syslog": SyslogFormatter,
}


def get_formatter(name: str) -> logging.Formatter:
    """Return an instance of the formatter registered under *name*."""
    cls = _FORMATTER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown log format '{name}'. Supported: {', '.join(sorted(_FORMATTER_REGISTRY))}")
    return cls()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HANDLER_MARKER = "_kcontrol_log_handler"


def _has_handler(marker_name: str) -> bool:
    return any(getattr(handler, marker_name, False) for handler in logging.getLogger().handlers)


def attach_otel_handler(handler: logging.Handler) -> None:
    root_logger = logging.getLogger()
    if _has_handler("_kcontrol_otel_handler"):
        return
    setattr(handler, "_kcontrol_otel_handler", True)
    root_logger.addHandler(handler)


def configure_logging(settings: object | None = None) -> None:
    global _FACTORY_CONFIGURED
    if settings is not None:
        _LOGGING_STATE["service"] = getattr(settings, "otel_service_name", None) or getattr(settings, "app_name", None)
        _LOGGING_STATE["environment"] = getattr(settings, "environment", None)

    root_logger = logging.getLogger()
    if not _FACTORY_CONFIGURED:
        logging.setLogRecordFactory(_record_factory)
        _FACTORY_CONFIGURED = True
    if not any(isinstance(filter_obj, ContextEnricher) for filter_obj in root_logger.filters):
        root_logger.addFilter(ContextEnricher())

    log_level_str = getattr(settings, "log_level", "INFO") if settings else "INFO"
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_format = getattr(settings, "log_format", "json") if settings else "json"

    if _has_handler(_HANDLER_MARKER) or _has_handler("_kcontrol_json_handler") or _has_handler("_kcontrol_text_handler"):
        root_logger.setLevel(log_level)
        _apply_level_overrides(settings)
        return

    handler = logging.StreamHandler()
    formatter = get_formatter(log_format)
    handler.setFormatter(formatter)
    setattr(handler, _HANDLER_MARKER, True)
    # Keep backward compat markers for tests
    if log_format == "json":
        setattr(handler, "_kcontrol_json_handler", True)
    elif log_format == "text":
        setattr(handler, "_kcontrol_text_handler", True)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    _apply_level_overrides(settings)


def _apply_level_overrides(settings: object | None) -> None:
    overrides = getattr(settings, "log_level_overrides", None)
    if not overrides:
        return
    for logger_name, level_str in overrides.items():
        level = getattr(logging, level_str, None)
        if level is not None:
            logging.getLogger(logger_name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
