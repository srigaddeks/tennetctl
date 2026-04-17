# 13-06a — Dashboards + SSE live-tail (BACKEND ONLY)

Partial plan summary. Frontend + Robot E2E split into later chunks.

## Migration

- **044** — `20260417_044_monitoring-dashboards.sql` (applied + moved to `01_migrated/`).
- Adds `10_fct_monitoring_dashboards`, `11_fct_monitoring_panels`,
  `v_monitoring_dashboards` (with `panel_count` via LEFT JOIN), `v_monitoring_panels`.
- Panels cascade-delete with parent via FK `ON DELETE CASCADE`.
- Partial UNIQUE `(org_id, owner_user_id, name) WHERE deleted_at IS NULL`.
- Full UP + DOWN + named constraints + COMMENT ON every column.

## Files created / modified

- 5-file sub-feature: `backend/02_features/05_monitoring/sub_features/05_dashboards/`
  (`__init__.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`).
- 5 node handlers under `.../05_dashboards/nodes/` (create/update/delete/get/list).
- SSE live-tail added to existing
  `backend/02_features/05_monitoring/sub_features/01_logs/routes.py`
  (`GET /v1/monitoring/logs/tail` + `_tail_generator`, `_decode_filter`, `_SSE_HEADERS`).
- `backend/02_features/05_monitoring/routes.py` — mounts dashboards router.
- `backend/02_features/05_monitoring/feature.manifest.yaml` — new
  `monitoring.dashboards` sub-feature (5 nodes, 10 routes) + `monitoring.logs.tail`
  route appended to existing logs sub-feature.
- `backend/02_features/05_monitoring/instrumentation/fastapi.py` — added
  `/v1/monitoring/logs/tail` to `_SKIP_PREFIXES` (BaseHTTPMiddleware buffers
  streams, so span emission is skipped for SSE routes).
- Tests: `tests/features/05_monitoring/test_dashboards_crud.py` (8),
  `test_panels_crud.py` (6), `test_logs_tail_sse.py` (5).

Total: 1 migration + 13 backend files created + 3 backend files modified + 3 test files.

## Pytest

- Monitoring suite: **139 passed** in 21s (was 120 before — +19 tests).
- Dashboards CRUD: 8/8.
- Panels CRUD: 6/6.
- SSE tail: 5/5.

## Pyright

0 errors, 0 warnings across the dashboards sub-feature, modified logs route,
and all new test files.

## Smoke tests

- `POST /v1/monitoring/dashboards` → 201 with full envelope.
- `GET  /v1/monitoring/dashboards` → 200, items list.
- `GET  /v1/monitoring/logs/tail` → 200, `content-type: text/event-stream`,
  streams initial `: ready\n\n` frame.

## Notable deviations / decisions

1. **SSE tests are generator-level, not end-to-end HTTP.** `httpx.ASGITransport`
   buffers the entire response body before returning (see
   `httpx._transports.asgi` — `response_complete` must fire before the stream
   is returned). Integration via ASGI is therefore impossible for an
   infinite-loop SSE endpoint. Tests drive `_tail_generator` directly,
   verifying ready-frame, data-frame-on-new-row, heartbeat, and filter
   rejection paths. A single sanity test asserts the route is mounted and
   SSE headers are declared. Real uvicorn smoke (curl) covers the full HTTP
   path.
2. **SSE routes bypass monitoring FastAPI middleware.** `BaseHTTPMiddleware`
   in Starlette 1.0 streams response bodies through an anyio task group —
   but the MonitoringMiddleware emits its span in the `finally` clause AFTER
   the stream closes, which can add latency to disconnects. Adding
   `/v1/monitoring/logs/tail` to `_SKIP_PREFIXES` keeps the streaming path
   hot.
3. **Soft-delete of dashboards does not touch panel rows.** The view
   `v_monitoring_dashboards` filters `deleted_at IS NULL`, so panels of
   soft-deleted dashboards become unreachable through any API. A future
   hard-delete job (not in scope here) is expected to clean up. Documented
   in `service.py` module docstring. The FK `ON DELETE CASCADE` still
   protects hard-delete integrity (verified in `test_panels_crud.py`).
4. **Node handlers receive `pool` via `ctx.extras["pool"]`.** This mirrors the
   existing `metrics.register` precedent. Node handlers remain runnable from
   the catalog runner without requiring a direct handle to the app.
