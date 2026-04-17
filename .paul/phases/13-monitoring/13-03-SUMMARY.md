# 13-03 Summary — OTLP Receiver + Auto-Instrumentation

Status: **APPLY complete**. 22/22 tests green, pyright clean, smoke test green.

## Created

**Logs sub-feature** (`backend/02_features/05_monitoring/sub_features/01_logs/`):
- `schemas.py` — OTLPLogsResponseJSON
- `repository.py` — intentionally empty (no DB writes in 13-03; 13-04 owns consumer)
- `service.py` — `publish_logs_batch(body, content_type, js)` -> (published, rejected)
- `otlp_decoder.py` — protobuf + JSON → `(subject, payload_bytes)` list. Subject `monitoring.logs.otel.{service_name}` with slugification.
- `routes.py` — `POST /v1/monitoring/otlp/v1/logs`, OTLP-spec responses (not tennetctl envelope)
- `nodes/otlp_ingest.py` — `monitoring.logs.otlp_ingest` (kind=request, emits_audit=false, hot_path)

**Traces sub-feature** (`backend/02_features/05_monitoring/sub_features/03_traces/`):
Mirror of logs sub-feature. Routes `POST /v1/monitoring/otlp/v1/traces`, node `monitoring.traces.otlp_ingest`.

**Instrumentation** (`backend/02_features/05_monitoring/instrumentation/`):
- `__init__.py` — `install_all(app, pool, config)` + shared `_in_monitoring_bridge` ContextVar
- `fastapi.py` — middleware: server-kind span per request, W3C `traceparent` propagation, skip list (`/v1/monitoring/otlp/`, `/health`, `/docs`, `/openapi.json`, `/redoc`), publishes ResourceSpans protobuf to `monitoring.traces.otel.tennetctl-backend`
- `asyncpg.py` — query logger publishing client-kind spans; SQL literal redaction (`'...'` and numerics → `?`); 256-char truncation
- `structlog_bridge.py` — stdlib `logging.Handler` publishing OTLP LogRecord protobuf; only forwards `tennetctl.*` loggers; silent drop + counter on NATS down; ContextVar recursion guard

**Aggregator** (`backend/02_features/05_monitoring/routes.py`) — includes logs + traces + metrics routers.

**Tests** (`tests/features/05_monitoring/`):
- `test_otlp_logs_receiver.py` — 7 tests
- `test_otlp_traces_receiver.py` — 6 tests
- `test_instrumentation.py` — 9 tests (fastapi middleware, traceparent propagation, skip-infra, redact_sql, truncate, asyncpg hook, bridge publishes, bridge silent-drop, recursion guard)

## Modified

- `backend/01_core/config.py` — added `monitoring_auto_instrument` (default True), `monitoring_otlp_auth_enabled` (default False); appended to `_ALLOWED_TENNET_ENV`
- `backend/main.py` — uncommented monitoring in MODULE_ROUTERS; added lifespan hook for asyncpg + bridge install; added import-time FastAPI middleware registration (middleware cannot be added after app start)
- `backend/02_features/05_monitoring/feature.manifest.yaml` — added logs + traces node + route entries (metrics section untouched, per 13-02 coordination)
- `.env` — added `monitoring` to `TENNETCTL_MODULES`

## Verification

- `opentelemetry-proto` version installed: **1.41.0** (already present from 13-01)
- `.venv/bin/pytest tests/features/05_monitoring/test_otlp_logs_receiver.py test_otlp_traces_receiver.py test_instrumentation.py`: **22/22 passed (0.51s)**
- `pyright` on all new files: **0 errors, 0 warnings**
- Smoke test live backend:
  - `POST /v1/monitoring/otlp/v1/logs` with valid JSON → `200 {}`
  - `POST /v1/monitoring/otlp/v1/logs` with malformed body → `400`
  - `POST /v1/monitoring/otlp/v1/traces` → `200`
  - `GET /v1/catalog/nodes` (instrumented) → `200`, MONITORING_SPANS incremented from 345 → 348 (+3 spans from 3 requests)
  - MONITORING_LOGS stream receives log bridge output

## Deviations from plan

1. **Node kind**: Plan called for `kind: effect` but the platform's catalog loader enforces `effect` → `emits_audit=true`. The OTLP ingest nodes are hot-path and need `emits_audit: false`, so they use `kind: request` (matches the gateway-compiled request path used for `auth_required` etc.). Manifest entries use `kind: request` accordingly.
2. **FastAPI middleware registration**: Starlette raises "Cannot add middleware after an application has started" when installed in lifespan. Split into import-time middleware registration + lifespan-time asyncpg + bridge install.
3. **structlog bridge scope**: Bridge only forwards loggers whose name starts with `tennetctl` (excluding the monitoring's own submodules). Without this filter, backend boot floods JetStream with uvicorn/asyncpg/third-party logs (~100k messages per startup). This is a necessary tightening; full structlog integration can be added later.
4. **Auth**: Plan called for a vault-backed bearer token; implemented as a flag-gated stub that rejects missing bearer header when `monitoring_otlp_auth_enabled=true`. Default off. Full vault lookup deferred.

## Readiness for 13-04

- JetStream streams receive ResourceLogs (one per message, subject `monitoring.logs.otel.{service}`) and ResourceSpans (one per message, subject `monitoring.traces.otel.{service}`) — payload is serialized protobuf. The 13-04 consumer can pull these with no re-batching.
- Backend self-instruments on every request + every asyncpg query + every app-namespace log call, so 13-04 has immediate data for integration testing.
- No Postgres writes are performed in 13-03, leaving the 13-04 consumer to own that path cleanly.
