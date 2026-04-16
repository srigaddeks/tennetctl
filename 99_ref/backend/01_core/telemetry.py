from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, is_dataclass
from functools import wraps
from importlib import import_module
from pathlib import Path
from types import FrameType
from typing import Any, ParamSpec, TypeVar, cast
import inspect
import logging
import sys
import threading

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute
from opentelemetry import propagate, trace, metrics as otel_metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import SpanKind, Status, StatusCode
from starlette.datastructures import Headers, MutableHeaders

try:
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
except ImportError:  # pragma: no cover
    OTLPMetricExporter = None


_settings_module = import_module("backend.00_config.settings")
_logging_module = import_module("backend.01_core.logging_utils")

Settings = _settings_module.Settings
BACKEND_DIR = _settings_module.BACKEND_DIR
load_settings = _settings_module.load_settings
attach_otel_handler = _logging_module.attach_otel_handler
bind_request_context = _logging_module.bind_request_context
bind_session_context = _logging_module.bind_session_context
configure_logging = _logging_module.configure_logging
get_logger = _logging_module.get_logger
reset_request_context = _logging_module.reset_request_context
reset_session_context = _logging_module.reset_session_context

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


PROJECT_DIR = BACKEND_DIR.parent
_BOOTSTRAPPED = False
_TRACE_PROVIDER_READY = False
_LOG_PROVIDER_READY = False
_METRICS_PROVIDER_READY = False
_FUNCTION_PROFILER_STARTED = False

_tracer_provider: TracerProvider | None = None
_logger_provider: LoggerProvider | None = None
_meter_provider: MeterProvider | None = None

# HTTP metrics (populated by _configure_metrics)
_http_request_counter = None
_http_request_duration = None

# Function metrics (populated by _configure_metrics)
_function_call_counter = None
_function_call_accumulator: "_FunctionCallAccumulator | None" = None

# Auth event metrics (populated by _configure_metrics)
_auth_event_counter = None

# Marker attribute set on functions wrapped by @instrument_function
_INSTRUMENTED_MARKER = "_otel_instrumented"

_SENSITIVE_NAME_PARTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "email",
    "username",
    "phone",
    "first_name",
    "last_name",
    "full_name",
    "address",
    "ip",
    "user_agent",
)


def _parse_headers(raw_headers: tuple[str, ...]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_headers:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _normalize_endpoint(raw_endpoint: str | None, *, insecure: bool) -> str | None:
    if raw_endpoint is None:
        return None
    endpoint = raw_endpoint.strip()
    if not endpoint:
        return None
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint.rstrip("/")
    scheme = "http" if insecure else "https"
    return f"{scheme}://{endpoint.rstrip('/')}"


def _signal_endpoint(
    *,
    specific_endpoint: str | None,
    shared_endpoint: str | None,
    suffix: str,
    insecure: bool,
) -> str | None:
    resolved_specific = _normalize_endpoint(specific_endpoint, insecure=insecure)
    if resolved_specific is not None:
        return resolved_specific
    resolved_shared = _normalize_endpoint(shared_endpoint, insecure=insecure)
    if resolved_shared is None:
        return None
    if resolved_shared.endswith(suffix):
        return resolved_shared
    return f"{resolved_shared}{suffix}"


def _resource(settings: Settings) -> Resource:
    attrs: dict[str, str] = {
        "service.name": settings.otel_service_name or settings.app_name,
        "service.version": settings.app_version,
        "deployment.environment.name": settings.environment,
    }
    # K8s metadata (injected via Downward API env vars in AKS)
    import os
    k8s_pod = os.getenv("K8S_POD_NAME")
    k8s_namespace = os.getenv("K8S_NAMESPACE")
    k8s_node = os.getenv("K8S_NODE_NAME")
    if k8s_pod:
        attrs["k8s.pod.name"] = k8s_pod
    if k8s_namespace:
        attrs["k8s.namespace.name"] = k8s_namespace
    if k8s_node:
        attrs["k8s.node.name"] = k8s_node
    return Resource.create(attrs)


def _relative_path(path_value: str) -> str:
    try:
        return str(Path(path_value).resolve().relative_to(PROJECT_DIR))
    except ValueError:
        return str(Path(path_value).resolve())


def _is_sensitive_key(name: str) -> bool:
    lowered = name.strip().lower()
    return any(part in lowered for part in _SENSITIVE_NAME_PARTS)


def _summarize_unknown(value: Any) -> str:
    value_type = type(value)
    return f"<{value_type.__module__}.{value_type.__qualname__}>"


def serialize_telemetry_value(value: Any, settings: Settings, *, field_name: str | None = None, depth: int = 0) -> Any:
    if field_name is not None and _is_sensitive_key(field_name):
        return "[REDACTED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) <= settings.otel_function_trace_max_value_length:
            return value
        return f"{value[:settings.otel_function_trace_max_value_length]}...(truncated)"
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if depth >= 2:
        return _summarize_unknown(value)
    if isinstance(value, type):
        return _summarize_unknown(value)
    if isinstance(value, Mapping):
        items = list(value.items())[: settings.otel_function_trace_max_collection_items]
        return {
            str(key): serialize_telemetry_value(
                item_value,
                settings,
                field_name=str(key),
                depth=depth + 1,
            )
            for key, item_value in items
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        max_items = int(settings.otel_function_trace_max_collection_items)
        values = list(value)[:max_items]
        return [
            serialize_telemetry_value(item, settings, depth=depth + 1)
            for item in values
        ]
    _model_dump_cls = getattr(type(value), "model_dump", None)
    if callable(_model_dump_cls) and not isinstance(value, type):
        try:
            return serialize_telemetry_value(_model_dump_cls(value), settings, depth=depth + 1)
        except TypeError:
            return _summarize_unknown(value)
    if is_dataclass(value):
        try:
            return serialize_telemetry_value(asdict(value), settings, depth=depth + 1)
        except (TypeError, AttributeError):
            return _summarize_unknown(value)
    return _summarize_unknown(value)


def _frame_arguments(frame: FrameType, settings: Settings) -> dict[str, Any]:
    if not settings.otel_function_trace_include_args:
        return {}
    arg_info = inspect.getargvalues(frame)
    payload: dict[str, Any] = {}
    for arg_name in arg_info.args:
        payload[arg_name] = serialize_telemetry_value(
            frame.f_locals.get(arg_name),
            settings,
            field_name=arg_name,
        )
    if arg_info.varargs:
        payload[arg_info.varargs] = serialize_telemetry_value(
            frame.f_locals.get(arg_info.varargs, ()),
            settings,
            field_name=arg_info.varargs,
        )
    if arg_info.keywords:
        payload[arg_info.keywords] = serialize_telemetry_value(
            frame.f_locals.get(arg_info.keywords, {}),
            settings,
            field_name=arg_info.keywords,
        )
    return payload


def _runtime_settings() -> Settings | None:
    try:
        return load_settings()
    except Exception:
        return None


def _serialize_runtime_value(value: Any, *, field_name: str | None = None) -> Any:
    settings = _runtime_settings()
    if settings is None:
        if field_name is not None and _is_sensitive_key(field_name):
            return "[REDACTED]"
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return value if len(value) <= 256 else f"{value[:256]}...(truncated)"
        if isinstance(value, bytes):
            return f"<bytes:{len(value)}>"
        return _summarize_unknown(value)
    return serialize_telemetry_value(value, settings, field_name=field_name)


def _bound_arguments(function: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    signature = inspect.signature(function)
    bound = signature.bind_partial(*args, **kwargs)
    return {
        name: _serialize_runtime_value(value, field_name=name)
        for name, value in bound.arguments.items()
    }


def instrument_function(
    *,
    span_name: str | None = None,
    action: str | None = None,
    logger_name: str = "backend.instrumentation",
    record_args: bool = True,
    record_result: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        logger = get_logger(logger_name)
        function_name = f"{function.__module__}.{function.__qualname__}"
        resolved_span_name = span_name or function_name
        resolved_action = action or "python.function"

        # Mark the original function so the profiler can skip duplicate logging
        setattr(function, _INSTRUMENTED_MARKER, True)

        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                payload: dict[str, Any] = {
                    "function_name": function.__name__,
                    "qualified_name": function_name,
                }
                if record_args:
                    payload["arguments"] = _bound_arguments(function, *args, **kwargs)
                with start_operation_span(resolved_span_name, attributes={"code.function": function_name}):
                    logger.info(
                        "python_function_started",
                        extra={"action": resolved_action, "outcome": "started", **payload},
                    )
                    try:
                        result = await cast(Callable[P, Any], function)(*args, **kwargs)
                    except Exception as exc:
                        trace.get_current_span().record_exception(exc)
                        trace.get_current_span().set_status(Status(StatusCode.ERROR))
                        logger.info(
                            "python_function_failed",
                            extra={
                                "action": resolved_action,
                                "outcome": "error",
                                **payload,
                                "exception": {
                                    "type": type(exc).__name__,
                                    "message": _serialize_runtime_value(str(exc)),
                                },
                            },
                        )
                        raise
                    if record_result:
                        payload["result"] = _serialize_runtime_value(result, field_name="result")
                    logger.info(
                        "python_function_completed",
                        extra={"action": resolved_action, "outcome": "success", **payload},
                    )
                    return cast(R, result)

            return cast(Callable[P, R], async_wrapper)

        @wraps(function)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            payload: dict[str, Any] = {
                "function_name": function.__name__,
                "qualified_name": function_name,
            }
            if record_args:
                payload["arguments"] = _bound_arguments(function, *args, **kwargs)
            with start_operation_span(resolved_span_name, attributes={"code.function": function_name}):
                logger.info(
                    "python_function_started",
                    extra={"action": resolved_action, "outcome": "started", **payload},
                )
                try:
                    result = function(*args, **kwargs)
                except Exception as exc:
                    trace.get_current_span().record_exception(exc)
                    trace.get_current_span().set_status(Status(StatusCode.ERROR))
                    logger.info(
                        "python_function_failed",
                        extra={
                            "action": resolved_action,
                            "outcome": "error",
                            **payload,
                            "exception": {
                                "type": type(exc).__name__,
                                "message": _serialize_runtime_value(str(exc)),
                            },
                        },
                    )
                    raise
                if record_result:
                    payload["result"] = _serialize_runtime_value(result, field_name="result")
                logger.info(
                    "python_function_completed",
                    extra={"action": resolved_action, "outcome": "success", **payload},
                )
                return result

        return cast(Callable[P, R], sync_wrapper)

    return decorator


def instrument_class_methods(
    *,
    namespace: str | None = None,
    include_private: bool = False,
    logger_name: str = "backend.instrumentation",
    exclude: tuple[str, ...] = ("__init__",),
) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        resolved_namespace = namespace or cls.__name__
        for name, value in vars(cls).items():
            if name in exclude:
                continue
            if name.startswith("__") and name.endswith("__"):
                continue
            if not include_private and name.startswith("_"):
                continue

            if isinstance(value, staticmethod):
                wrapped = instrument_function(
                    span_name=f"{resolved_namespace}.{name}",
                    action=f"{resolved_namespace}.{name}",
                    logger_name=logger_name,
                )(value.__func__)
                setattr(cls, name, staticmethod(wrapped))
                continue

            if isinstance(value, classmethod):
                wrapped = instrument_function(
                    span_name=f"{resolved_namespace}.{name}",
                    action=f"{resolved_namespace}.{name}",
                    logger_name=logger_name,
                )(value.__func__)
                setattr(cls, name, classmethod(wrapped))
                continue

            if inspect.isfunction(value):
                wrapped = instrument_function(
                    span_name=f"{resolved_namespace}.{name}",
                    action=f"{resolved_namespace}.{name}",
                    logger_name=logger_name,
                )(value)
                setattr(cls, name, wrapped)
        return cls

    return decorator


def instrument_module_functions(
    module_globals: dict[str, Any],
    *,
    namespace: str,
    include_private: bool = False,
    logger_name: str = "backend.instrumentation",
    exclude: tuple[str, ...] = (),
) -> None:
    module_name = str(module_globals.get("__name__", ""))
    for name, value in list(module_globals.items()):
        if name in exclude:
            continue
        if not include_private and name.startswith("_"):
            continue
        if not inspect.isfunction(value):
            continue
        if getattr(value, "__module__", None) != module_name:
            continue
        module_globals[name] = instrument_function(
            span_name=f"{namespace}.{name}",
            action=f"{namespace}.{name}",
            logger_name=logger_name,
        )(value)


class InstrumentedAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Any]:
        original_handler = super().get_route_handler()
        logger = get_logger("backend.fastapi")
        route_name = self.name or self.path
        methods = ",".join(sorted(self.methods or []))

        async def instrumented_handler(request: Request):
            with start_operation_span(
                f"fastapi.endpoint.{route_name}",
                attributes={
                    "fastapi.route_name": route_name,
                    "http.route": self.path,
                    "http.request.method": request.method,
                },
            ):
                logger.info(
                    "fastapi_endpoint_started",
                    extra={
                        "action": "fastapi.endpoint",
                        "outcome": "started",
                        "fastapi_route_name": route_name,
                        "http_route": self.path,
                        "http_method": request.method,
                        "http_methods_registered": methods,
                    },
                )
                try:
                    response = await original_handler(request)
                except Exception as exc:
                    trace.get_current_span().record_exception(exc)
                    trace.get_current_span().set_status(Status(StatusCode.ERROR))
                    logger.info(
                        "fastapi_endpoint_failed",
                        extra={
                            "action": "fastapi.endpoint",
                            "outcome": "error",
                            "fastapi_route_name": route_name,
                            "http_route": self.path,
                            "http_method": request.method,
                            "exception": {
                                "type": type(exc).__name__,
                                "message": _serialize_runtime_value(str(exc)),
                            },
                        },
                    )
                    raise
                logger.info(
                    "fastapi_endpoint_completed",
                    extra={
                        "action": "fastapi.endpoint",
                        "outcome": "success",
                        "fastapi_route_name": route_name,
                        "http_route": self.path,
                        "http_method": request.method,
                        "http_status_code": getattr(response, "status_code", None),
                    },
                )
                return response

        return instrumented_handler


class InstrumentedAPIRouter(APIRouter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("route_class", InstrumentedAPIRoute)
        super().__init__(*args, **kwargs)


def _qualified_name(frame: FrameType) -> str:
    function_name = frame.f_code.co_name
    self_obj = frame.f_locals.get("self")
    cls_obj = frame.f_locals.get("cls")
    if self_obj is not None:
        return f"{type(self_obj).__name__}.{function_name}"
    if cls_obj is not None and isinstance(cls_obj, type):
        return f"{cls_obj.__name__}.{function_name}"
    return function_name


class BackendFunctionProfiler:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger("backend.telemetry.function")
        self._backend_root = BACKEND_DIR.resolve()
        self._thread_state = threading.local()

    def _is_excluded(self, frame: FrameType) -> bool:
        module_name = str(frame.f_globals.get("__name__", ""))
        if any(module_name.startswith(prefix) for prefix in self._settings.otel_function_trace_excluded_module_prefixes):
            return True
        frame_path = str(Path(frame.f_code.co_filename).resolve())
        if any(fragment and fragment in frame_path for fragment in self._settings.otel_function_trace_excluded_path_fragments):
            return True
        return False

    def _is_backend_frame(self, frame: FrameType) -> bool:
        try:
            frame_path = Path(frame.f_code.co_filename).resolve()
        except Exception:
            return False
        return frame_path.is_file() and self._backend_root in frame_path.parents and not self._is_excluded(frame)

    def _log(self, *, action: str, outcome: str, payload: dict[str, Any]) -> None:
        if getattr(self._thread_state, "active", False):
            return
        self._thread_state.active = True
        try:
            self._logger.info(
                action,
                extra={
                    "action": action,
                    "outcome": outcome,
                    **payload,
                },
            )
        finally:
            self._thread_state.active = False

    def _is_already_instrumented(self, frame: FrameType) -> bool:
        """Check if the function is already decorated with @instrument_function."""
        func_obj = frame.f_globals.get(frame.f_code.co_name)
        if func_obj is not None and getattr(func_obj, _INSTRUMENTED_MARKER, False):
            return True
        # Check for method on self/cls
        self_obj = frame.f_locals.get("self")
        if self_obj is not None:
            method = getattr(type(self_obj), frame.f_code.co_name, None)
            if method is not None and getattr(method, _INSTRUMENTED_MARKER, False):
                return True
        return False

    def profile(self, frame: FrameType, event: str, arg: Any) -> None:
        if event not in {"call", "return", "exception"}:
            return
        if not self._is_backend_frame(frame):
            return

        payload = {
            "code_path": _relative_path(frame.f_code.co_filename),
            "module_name": str(frame.f_globals.get("__name__", "")),
            "function_name": frame.f_code.co_name,
            "qualified_name": _qualified_name(frame),
            "line_number": frame.f_code.co_firstlineno,
        }

        # Always count function calls for metrics (even if decorated)
        if event == "call" and _function_call_accumulator is not None:
            _function_call_accumulator.increment(
                module=payload["module_name"],
                function=payload["function_name"],
                qualified_name=payload["qualified_name"],
                filepath=payload["code_path"],
            )

        # Skip logging for functions already decorated with @instrument_function
        # (they create their own spans and log entries via the decorator)
        skip_logging = self._is_already_instrumented(frame)

        if event == "call":
            if not skip_logging:
                payload["arguments"] = _frame_arguments(frame, self._settings)
                self._log(action="python.function.call", outcome="started", payload=payload)
            return

        if event == "return":
            if not skip_logging:
                if self._settings.otel_function_trace_include_return:
                    payload["result"] = serialize_telemetry_value(arg, self._settings)
                self._log(action="python.function.return", outcome="success", payload=payload)
            return

        if not skip_logging:
            if self._settings.otel_function_trace_include_exceptions:
                exc_type, exc_value, _ = arg
                payload["exception"] = {
                    "type": getattr(exc_type, "__name__", "Exception"),
                    "message": serialize_telemetry_value(str(exc_value), self._settings),
                }
            self._log(action="python.function.exception", outcome="error", payload=payload)


class _FunctionCallAccumulator:
    """Thread-safe in-memory accumulator that flushes function call counts to an OTel counter periodically."""

    def __init__(self, counter, flush_interval: int = 15) -> None:
        self._counter = counter
        self._flush_interval = flush_interval
        self._counts: dict[tuple[str, str, str, str], int] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._running = False

    def increment(self, module: str, function: str, qualified_name: str, filepath: str) -> None:
        key = (module, function, qualified_name, filepath)
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + 1

    def flush(self) -> None:
        with self._lock:
            snapshot = self._counts
            self._counts = {}
        for (module, function, qname, fpath), count in snapshot.items():
            self._counter.add(count, {
                "code.module": module,
                "code.function": function,
                "code.qualified_name": qname,
                "code.filepath": fpath,
            })
        if self._running:
            self._schedule_flush()

    def start(self) -> None:
        self._running = True
        self._schedule_flush()

    def stop(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()
        self.flush()

    def _schedule_flush(self) -> None:
        self._timer = threading.Timer(self._flush_interval, self.flush)
        self._timer.daemon = True
        self._timer.start()


def _configure_traces(settings: Settings) -> None:
    global _TRACE_PROVIDER_READY, _tracer_provider
    if _TRACE_PROVIDER_READY or not settings.otel_enabled or not settings.otel_traces_enabled:
        return

    tracer_provider = TracerProvider(
        resource=_resource(settings),
        sampler=ParentBasedTraceIdRatio(settings.otel_sample_ratio),
    )
    traces_endpoint = _signal_endpoint(
        specific_endpoint=settings.otel_exporter_otlp_traces_endpoint,
        shared_endpoint=settings.otel_exporter_otlp_endpoint,
        suffix="/v1/traces",
        insecure=settings.otel_exporter_otlp_insecure,
    )
    if traces_endpoint is not None:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=traces_endpoint,
                    headers=_parse_headers(settings.otel_exporter_otlp_headers),
                    timeout=settings.otel_exporter_otlp_timeout_seconds,
                )
            )
        )
    trace.set_tracer_provider(tracer_provider)
    _tracer_provider = tracer_provider
    _TRACE_PROVIDER_READY = True


def _configure_log_export(settings: Settings) -> None:
    global _LOG_PROVIDER_READY, _logger_provider
    if _LOG_PROVIDER_READY or not settings.otel_enabled or not settings.otel_logs_enabled:
        return

    logs_endpoint = _signal_endpoint(
        specific_endpoint=settings.otel_exporter_otlp_logs_endpoint,
        shared_endpoint=settings.otel_exporter_otlp_endpoint,
        suffix="/v1/logs",
        insecure=settings.otel_exporter_otlp_insecure,
    )
    if logs_endpoint is None:
        return

    logger_provider = LoggerProvider(resource=_resource(settings))
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=logs_endpoint,
                headers=_parse_headers(settings.otel_exporter_otlp_headers),
                timeout=settings.otel_exporter_otlp_timeout_seconds,
            )
        )
    )
    set_logger_provider(logger_provider)
    attach_otel_handler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))
    _logger_provider = logger_provider
    _LOG_PROVIDER_READY = True


def _configure_function_profiler(settings: Settings) -> None:
    global _FUNCTION_PROFILER_STARTED
    if _FUNCTION_PROFILER_STARTED or not settings.otel_function_trace_enabled:
        return
    profiler = BackendFunctionProfiler(settings)
    sys.setprofile(profiler.profile)
    threading.setprofile(profiler.profile)
    if _function_call_accumulator is not None:
        _function_call_accumulator.start()
    _FUNCTION_PROFILER_STARTED = True


def _configure_metrics(settings: Settings) -> None:
    global _METRICS_PROVIDER_READY, _meter_provider, _http_request_counter, _http_request_duration, _auth_event_counter
    if _METRICS_PROVIDER_READY or not settings.otel_enabled or not settings.otel_metrics_enabled:
        return

    metrics_endpoint = _signal_endpoint(
        specific_endpoint=None,
        shared_endpoint=settings.otel_exporter_otlp_endpoint,
        suffix="/v1/metrics",
        insecure=settings.otel_exporter_otlp_insecure,
    )

    readers = []
    if metrics_endpoint is not None and OTLPMetricExporter is not None:
        readers.append(
            PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=metrics_endpoint,
                    headers=_parse_headers(settings.otel_exporter_otlp_headers),
                    timeout=settings.otel_exporter_otlp_timeout_seconds,
                ),
                export_interval_millis=30_000,
            )
        )

    meter_provider = MeterProvider(resource=_resource(settings), metric_readers=readers)
    otel_metrics.set_meter_provider(meter_provider)
    _meter_provider = meter_provider

    meter = meter_provider.get_meter("backend.http", version=settings.app_version)
    _http_request_counter = meter.create_counter(
        "http.server.request.count",
        description="Total HTTP requests",
        unit="1",
    )
    _http_request_duration = meter.create_histogram(
        "http.server.request.duration",
        description="HTTP request duration",
        unit="s",
    )

    auth_meter = meter_provider.get_meter("backend.auth", version=settings.app_version)
    _auth_event_counter = auth_meter.create_counter(
        "auth.event.count",
        description="Authentication and session events",
        unit="1",
    )

    # Function call counter for stale function detection
    if settings.otel_function_metrics_enabled:
        function_meter = meter_provider.get_meter("backend.function", version=settings.app_version)
        _function_call_counter = function_meter.create_counter(
            "backend.function.call.count",
            description="Total function calls in backend code",
            unit="1",
        )
        _function_call_accumulator = _FunctionCallAccumulator(
            _function_call_counter,
            flush_interval=settings.otel_function_metrics_flush_interval_seconds,
        )

    _METRICS_PROVIDER_READY = True


def shutdown_observability() -> None:
    global _tracer_provider, _logger_provider, _meter_provider, _function_call_accumulator
    logger = get_logger("backend.telemetry")
    # Flush and stop function metrics accumulator before provider shutdown
    if _function_call_accumulator is not None:
        _function_call_accumulator.stop()
        _function_call_accumulator = None
    for name, provider in [
        ("tracer", _tracer_provider),
        ("logger", _logger_provider),
        ("meter", _meter_provider),
    ]:
        if provider is None:
            continue
        try:
            if hasattr(provider, "force_flush"):
                provider.force_flush(timeout_millis=5_000)
            if hasattr(provider, "shutdown"):
                provider.shutdown()
            logger.info(
                f"observability.{name}_provider_shutdown",
                extra={"action": f"observability.{name}.shutdown", "outcome": "success"},
            )
        except Exception:
            logger.warning(
                f"observability.{name}_provider_shutdown_failed",
                extra={"action": f"observability.{name}.shutdown", "outcome": "error"},
            )
    _tracer_provider = None
    _logger_provider = None
    _meter_provider = None


def _configure_glitchtip(settings: Settings) -> None:
    """Initialize Sentry SDK for GlitchTip error tracking."""
    if not settings.glitchtip_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        get_logger("backend.telemetry").warning(
            "glitchtip.sentry_sdk_not_installed",
            extra={"action": "glitchtip.init", "outcome": "skipped",
                   "reason": "sentry-sdk[fastapi] not installed"},
        )
        return
    sentry_sdk.init(
        dsn=settings.glitchtip_dsn,
        traces_sample_rate=settings.glitchtip_traces_sample_rate,
        environment=settings.environment,
        release=settings.app_version,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
        send_default_pii=False,
    )
    get_logger("backend.telemetry").info(
        "glitchtip.initialized",
        extra={"action": "glitchtip.init", "outcome": "success",
               "environment": settings.environment},
    )


def configure_observability(settings: Settings) -> None:
    global _BOOTSTRAPPED
    configure_logging(settings)
    _configure_traces(settings)
    _configure_log_export(settings)
    _configure_metrics(settings)
    _configure_function_profiler(settings)
    _configure_glitchtip(settings)
    if _BOOTSTRAPPED:
        return
    get_logger("backend.telemetry").info(
        "observability.started",
        extra={
            "action": "observability.started",
            "outcome": "success",
            "otel_enabled": settings.otel_enabled,
            "traces_enabled": settings.otel_enabled and settings.otel_traces_enabled,
            "logs_enabled": settings.otel_enabled and settings.otel_logs_enabled,
            "metrics_enabled": settings.otel_enabled and settings.otel_metrics_enabled,
            "function_trace_enabled": settings.otel_function_trace_enabled,
            "function_metrics_enabled": settings.otel_function_metrics_enabled,
            "glitchtip_enabled": settings.glitchtip_dsn is not None,
        },
    )
    _BOOTSTRAPPED = True


def _build_endpoint_route_map(app) -> dict[int, str]:
    """Build a map from endpoint function id to route template path."""
    route_map: dict[int, str] = {}
    for route in getattr(app, "routes", []):
        endpoint = getattr(route, "endpoint", None)
        path = getattr(route, "path", None)
        if endpoint is not None and path is not None:
            route_map[id(endpoint)] = path
    return route_map


def instrument_fastapi_app(app) -> None:
    if getattr(app.state, "otel_fastapi_instrumented", False):
        return

    endpoint_route_map = _build_endpoint_route_map(app)

    class HttpObservabilityMiddleware:
        def __init__(self, inner_app) -> None:
            self.app = inner_app
            self.tracer = trace.get_tracer("backend.http")
            self._endpoint_route_map = endpoint_route_map

        async def __call__(self, scope, receive, send) -> None:
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return

            headers = Headers(scope=scope)
            request_id = headers.get("x-request-id") or str(__import__("uuid").uuid4())
            scope.setdefault("state", {})["request_id"] = request_id
            request_token = bind_request_context(request_id)
            extracted_context = propagate.extract(headers)
            method = scope.get("method", "HTTP")
            path = scope.get("path", "/")
            span_name = f"{method} {path}"
            response_status = [0]

            async def send_wrapper(message) -> None:
                if message["type"] == "http.response.start":
                    mutable_headers = MutableHeaders(raw=message["headers"])
                    mutable_headers["X-Request-ID"] = request_id
                    if path.startswith("/api/v1/auth/local/"):
                        mutable_headers["Cache-Control"] = "no-store"
                        mutable_headers["Pragma"] = "no-cache"
                    status_code = message.get("status")
                    if status_code is not None:
                        response_status[0] = status_code
                        current_span = trace.get_current_span()
                        if current_span is not None:
                            current_span.set_attribute("http.response.status_code", status_code)
                            if status_code >= 500:
                                current_span.set_status(Status(StatusCode.ERROR))
                await send(message)

            import time as _time
            start = _time.monotonic()
            try:
                with self.tracer.start_as_current_span(
                    span_name,
                    context=extracted_context,
                    kind=SpanKind.SERVER,
                    attributes={
                        "http.request.method": method,
                        "url.path": path,
                    },
                ) as span:
                    try:
                        await self.app(scope, receive, send_wrapper)
                    except Exception as exc:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR))
                        raise
                    finally:
                        # Resolve route template after Starlette routing sets scope["endpoint"]
                        endpoint = scope.get("endpoint")
                        if endpoint is not None:
                            route_template = self._endpoint_route_map.get(id(endpoint), path)
                        else:
                            route_template = "UNMATCHED" if response_status[0] == 404 else path
                        span.set_attribute("http.route", route_template)
                        span.update_name(f"{method} {route_template}")
            finally:
                duration = _time.monotonic() - start
                # Use resolved route template for metrics (falls back to raw path)
                endpoint = scope.get("endpoint")
                if endpoint is not None:
                    resolved_route = self._endpoint_route_map.get(id(endpoint), path)
                else:
                    resolved_route = "UNMATCHED" if response_status[0] == 404 else path
                metric_attrs = {
                    "http.request.method": method,
                    "http.route": resolved_route,
                    "http.response.status_code": response_status[0],
                }
                if _http_request_counter is not None:
                    _http_request_counter.add(1, metric_attrs)
                if _http_request_duration is not None:
                    _http_request_duration.record(duration, metric_attrs)
                # Reset context vars bound during request (session bound by auth dependency)
                _logging_module._SESSION_ID.set(None)
                reset_request_context(request_token)

    app.add_middleware(HttpObservabilityMiddleware)

    app.state.otel_fastapi_instrumented = True


def start_operation_span(name: str, *, attributes: Mapping[str, Any] | None = None):
    tracer = trace.get_tracer("backend.operation")
    return tracer.start_as_current_span(name, attributes=dict(attributes or {}))


def record_auth_event(event_type: str, *, outcome: str = "success", tenant_key: str = "") -> None:
    """Increment the auth.event.count metric counter.

    Args:
        event_type: The event type (e.g. "login", "logout", "register", "refresh").
        outcome: "success" or "failure".
        tenant_key: Tenant identifier for multi-tenant filtering.
    """
    if _auth_event_counter is not None:
        _auth_event_counter.add(1, {
            "auth.event_type": event_type,
            "auth.outcome": outcome,
            "auth.tenant_key": tenant_key,
        })
