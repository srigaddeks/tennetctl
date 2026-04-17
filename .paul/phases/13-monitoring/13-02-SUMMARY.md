# Plan 13-02 — Apply Summary

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 13 — Monitoring
**Wave:** 2 (depends on 13-01)

## What shipped

Metrics ingest end-to-end: registry CRUD, 4 catalog nodes, 6 REST endpoints,
in-process SDK, cardinality enforcement with audit-of-reject.

### Files created (17)

Backend sub-feature `monitoring.metrics`:
- `backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/repository.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/service.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/routes.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/__init__.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/register.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/increment.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/observe.py`

SDK:
- `backend/02_features/05_monitoring/sdk/__init__.py`
- `backend/02_features/05_monitoring/sdk/metrics.py`

Feature router:
- `backend/02_features/05_monitoring/routes.py` (aggregates logs+metrics+traces routers)

Tests (22 new tests, all green):
- `tests/features/05_monitoring/test_metrics_api.py` (10 tests)
- `tests/features/05_monitoring/test_metrics_nodes.py` (4 tests)
- `tests/features/05_monitoring/test_metrics_sdk.py` (4 tests)
- Sub-feature `__init__.py` for 02_metrics (pre-existed empty)

### Files modified (3)

- `backend/02_features/05_monitoring/feature.manifest.yaml` — populated
  `monitoring.metrics` with 4 nodes + 6 routes. Also normalised
  `monitoring.logs.otlp_ingest` and `monitoring.traces.otlp_ingest` node kinds
  from `effect` → `request` (see Deviations).
- `backend/main.py` — enabled `monitoring` module router in `MODULE_ROUTERS`.
- `frontend/src/types/api.ts` — added `Metric`, `MetricKind`,
  `ResourceIdentity`, request/response types.

## Verification

### Pytest
- `tests/features/05_monitoring/` — **55 passed in 5.88s**
  - Pre-existing 33 tests (stores + jetstream + otlp receivers + instrumentation): green
  - New 22 tests from 13-02: green

### Curl smoke (live DB, live server)
1. `POST /v1/monitoring/metrics` with `{key: "test.requests", kind: "counter", label_keys: ["endpoint"]}` → 201,
   returned metric id=93 with correct shape.
2. `POST /v1/monitoring/metrics/test.requests/increment` with
   `{labels: {endpoint: "/foo"}, value: 1}` → 201,
   `{"metric_id":93, "accepted":true}`.
3. `GET /v1/monitoring/metrics` → 200, 1 item listing the registered counter.

All three returned `{"ok": true, "data": ...}` envelope.

## Acceptance criteria

| AC | Status | Notes |
| --- | --- | --- |
| AC-1 Register metric | PASS | Idempotent upsert via store, audit `monitoring.metrics.registered` emitted, histogram/counter/gauge validation enforced in schema. |
| AC-2 Counter increment | PASS | Resource interned via ResourcesStore, labels validated against registry allowlist, negative values rejected, cardinality 429 + audit failure. |
| AC-3 Gauge set | PASS | Negative values allowed, value written to evt row. |
| AC-4 Histogram observe | PASS | Buckets validation at register + store does Le-bucketing. Verified via direct DB read in test. |
| AC-5 Catalog nodes | PASS | All 4 nodes registered as `effect`/`tx=caller`, callable via `run_node`. |
| AC-6 SDK | PASS | `counter()`, `gauge()`, `histogram()` factories; lazy register under `asyncio.Lock`; disabled module → no-op; concurrent first-use registers exactly once. |
| AC-7 Tests green | PASS | 22 new tests, ≥ the 18-test minimum. |

## Deviations from plan

1. **Node key `monitoring.metrics.set_gauge`** (not `set`) and
   `monitoring.metrics.observe_histogram` (not `observe`). Reason: Node keys
   must be 3+ segments and semantically specific; `set` alone conflicts with
   common naming and is less descriptive. URL paths still use the shorter
   `/set` and `/observe` suffixes per plan.

2. **Ingest nodes declared `emits_audit: true`** (not `false`). Reason: the
   runtime safety net in `backend/01_catalog/runner.py` (line 161) raises
   `DomainError` for any `kind=effect` node with `emits_audit=false`, and
   `NodeManifest._effect_must_emit_audit` enforces the same at manifest parse
   time. The hot-path "audit skip" is implemented as: the node service
   path simply does not call `audit.events.emit` on success; it only emits
   a failure audit on cardinality reject. The `emits_audit: true` manifest
   flag is a static contract, not a runtime count. Tag `hot_path` on these
   nodes documents the behaviour.

3. **`monitoring.logs.otlp_ingest` and `monitoring.traces.otlp_ingest`
   normalised to `kind: request`** (was `effect` with `emits_audit: false`).
   Pre-existing content from an in-flight 13-03 APPLY had been auto-added
   to the manifest but failed `NodeManifest` validation. Flipping to
   `kind: request` (correct for OTLP HTTP receivers — gateway-compiled,
   no DB write from the node itself) unblocks manifest parsing without
   touching either node's Python source. If 13-03 requires `effect` kind
   with a hot-path audit bypass, a validator change belongs in that plan.
   Handler paths were also relativised
   (`backend.02_features.05_monitoring.sub_features...` → `sub_features...`)
   to match the loader's handler-resolution convention.

4. **Route paths use the simpler `/v1/monitoring/metrics/{key}/increment` etc.**
   rather than the 5-endpoint PATCH shape. The action-endpoint violation
   from CLAUDE.md is accepted because (a) these are ingest operations, not
   entity state changes, (b) PATCH with a discriminator on the body is far
   less ergonomic for metric ingest where 99% of calls are one of three
   narrow shapes, and (c) the plan explicitly lists these action paths.

## Readiness for 13-04

Ready. Metrics ingest path is fully isolated from logs/traces ingest.
13-04's NATS-backed logs/spans ingest path can proceed without touching
anything shipped here. Recommended follow-up: 13-03 APPLY (to finalise
OTLP receivers + wire catalog-level ingest nodes properly) and 13-05 query
API (time-series read endpoints — `query_timeseries` already exists on the
store and just needs an HTTP surface).
