# OTel Setup

Last updated: 2026-03-13

## Purpose

This document is the practical setup guide for OpenTelemetry logging and tracing in the backend.
It explains:

- how observability is enabled
- which environment variables control it
- how to instrument FastAPI endpoints
- how to instrument service classes
- how to instrument module-level helper functions
- how nested internal function calls behave

This document covers operational telemetry only.
Audit events remain separate and continue to use the audit writer and audit tables.

## Current Wiring

The backend observability entry points are in:

- `backend/01_core/telemetry.py`
- `backend/01_core/logging_utils.py`
- `backend/01_core/application.py`

The application boot flow is:

1. `create_app()` calls `configure_observability(settings)`
2. `instrument_fastapi_app(app)` adds request-level HTTP tracing
3. log records are enriched with `request_id`, `trace_id`, and `span_id`
4. manual and automatic wrappers create child spans inside the request span

## Environment Variables

The backend reads these observability settings from `backend/00_config/settings.py`.

Core toggles:

- `OTEL_ENABLED`
- `OTEL_TRACES_ENABLED`
- `OTEL_LOGS_ENABLED`
- `OTEL_FUNCTION_TRACE_ENABLED`

Exporter configuration:

- `OTEL_EXPORTER_OTLP_PROTOCOL`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
- `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`
- `OTEL_EXPORTER_OTLP_HEADERS`
- `OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS`
- `OTEL_EXPORTER_OTLP_INSECURE`

Sampling:

- `OTEL_SAMPLE_RATIO`

Function trace controls:

- `OTEL_FUNCTION_TRACE_INCLUDE_ARGS`
- `OTEL_FUNCTION_TRACE_INCLUDE_RETURN`
- `OTEL_FUNCTION_TRACE_INCLUDE_EXCEPTIONS`
- `OTEL_FUNCTION_TRACE_MAX_VALUE_LENGTH`
- `OTEL_FUNCTION_TRACE_MAX_COLLECTION_ITEMS`
- `OTEL_FUNCTION_TRACE_EXCLUDED_MODULE_PREFIXES`
- `OTEL_FUNCTION_TRACE_EXCLUDED_PATH_FRAGMENTS`

Minimal local example:

```env
OTEL_ENABLED=true
OTEL_TRACES_ENABLED=true
OTEL_LOGS_ENABLED=true
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SAMPLE_RATIO=1.0
```

## Recommended Instrumentation Pattern

Use the framework root span for inbound HTTP requests, then add child spans automatically at the code boundaries you own.

Use these helpers from `backend/01_core/telemetry.py`:

- `InstrumentedAPIRouter`
- `instrument_class_methods`
- `instrument_module_functions`
- `instrument_function`
- `start_operation_span`

### FastAPI Routers

Use `InstrumentedAPIRouter` instead of `APIRouter`.
This instruments every endpoint attached to that router.

```python
from importlib import import_module

telemetry = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = telemetry.InstrumentedAPIRouter

router = InstrumentedAPIRouter(prefix="/api/v1/orders", tags=["orders"])
```

Effect:

- creates a span per endpoint execution
- logs endpoint start, success, and failure
- keeps the endpoint span nested under the incoming HTTP request span

### Service Classes

Use `@instrument_class_methods(...)` on service classes.

```python
from importlib import import_module

telemetry = import_module("backend.01_core.telemetry")
instrument_class_methods = telemetry.instrument_class_methods


@instrument_class_methods(
    namespace="orders.service",
    logger_name="backend.orders.instrumentation",
    include_private=True,
)
class OrderService:
    async def create_order(self, payload) -> dict:
        return await self._save_order(payload)

    async def _save_order(self, payload) -> dict:
        return {"status": "ok"}
```

Effect:

- instruments all public methods
- with `include_private=True`, also instruments internal methods like `_save_order`
- internal calls become child spans under the active endpoint or request span

### Module-Level Helper Functions

Use `instrument_module_functions(globals(), ...)` once at the bottom of the module.

```python
from importlib import import_module

telemetry = import_module("backend.01_core.telemetry")
instrument_module_functions = telemetry.instrument_module_functions


async def build_order_payload(api_key: str) -> dict:
    return {"status": "ok"}


instrument_module_functions(
    globals(),
    namespace="orders.helpers",
    include_private=True,
)
```

Effect:

- instruments module helper functions without decorating each one manually
- supports internal helpers such as `_normalize_input`

### Single Function

Use `@instrument_function(...)` when you want explicit control for one function.

```python
from importlib import import_module

telemetry = import_module("backend.01_core.telemetry")
instrument_function = telemetry.instrument_function


@instrument_function(
    span_name="orders.charge_card",
    action="orders.charge_card",
    logger_name="backend.orders.instrumentation",
)
async def charge_card(token: str) -> dict:
    return {"status": "ok"}
```

## Internal Function Calls

If a function is instrumented and it is called from inside another instrumented function, the called function creates a child span under the current active span.

Example call chain:

`HTTP request -> FastAPI endpoint -> service method -> internal helper`

If each layer is instrumented:

- the HTTP request has the root server span
- the endpoint has a child span
- the service method has a child span
- the internal helper has another child span

This is the clean way to get deep function-level traces without manually creating spans inside every call site.

## Redaction Behavior

Telemetry serialization already redacts sensitive-looking fields.
Examples include names containing:

- `password`
- `secret`
- `token`
- `authorization`
- `cookie`
- `api_key`
- `email`
- `username`
- `phone`
- `ip`
- `user_agent`

This applies to logged arguments and logged results when those fields are named clearly.

## When To Use Which Option

Use `InstrumentedAPIRouter` for:

- FastAPI route modules

Use `instrument_class_methods(..., include_private=True)` for:

- service classes
- manager classes
- policy classes

Use `instrument_module_functions(globals(), ..., include_private=True)` for:

- helper modules
- pure function modules
- validation and transformation modules

Use `@instrument_function(...)` for:

- one-off explicit wrapping
- functions that need a custom span name or action

Use `start_operation_span(...)` directly for:

- narrow manual spans around a specific integration boundary
- DB, cache, queue, external API, or migration steps

## Limits

This setup does not automatically instrument:

- lambdas
- nested local functions declared inside another function
- third-party library internals

If you need those covered, either move them to module or class scope, or use the profiler-based fallback.

## Profiler-Based Fallback

`OTEL_FUNCTION_TRACE_ENABLED=true` enables the Python profiler-based function trace path.

Use it when you want very broad coverage with minimal code changes.
Do not treat it as the preferred production default for all workloads because it is noisier and more expensive than targeted decorators.

Recommended use:

- local debugging
- short-lived diagnostics
- controlled staging verification

Preferred long-term production approach:

- `InstrumentedAPIRouter`
- `instrument_class_methods`
- `instrument_module_functions`
- selective `start_operation_span`

## Standard Module Pattern

For most backend feature code, use this pattern:

1. router files use `InstrumentedAPIRouter`
2. service files use `@instrument_class_methods(..., include_private=True)`
3. helper modules call `instrument_module_functions(globals(), ..., include_private=True)`
4. integration-heavy steps use `start_operation_span(...)` where extra detail is useful

This gives broad coverage without forcing every function to be wrapped manually.

## Testing

Verify observability on real execution paths.

Current direct tests live in:

- `backend/90_tests/test_core_observability.py`
- `backend/90_tests/test_auth_api.py`

Minimum checks:

- request path creates spans
- endpoint wrapper logs start and completion
- service methods create nested spans
- internal helper methods create child spans when instrumented
- sensitive fields are redacted
- failure paths record exceptions

## Example Adoption Checklist

For a new feature module:

1. import `InstrumentedAPIRouter` and replace `APIRouter`
2. decorate the service class with `@instrument_class_methods(..., include_private=True)`
3. instrument helper modules with `instrument_module_functions(globals(), ..., include_private=True)`
4. add focused tests for one successful path and one failure path

## Summary

If you want easy instrumentation for almost every function you own:

- use `InstrumentedAPIRouter` for FastAPI
- use `instrument_class_methods(..., include_private=True)` for classes
- use `instrument_module_functions(globals(), ..., include_private=True)` for helper modules

That covers endpoint functions, internal service calls, and internal helper calls cleanly and consistently.
