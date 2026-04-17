---
phase: 13-monitoring
plan: 05
status: complete
date: 2026-04-17
---

# 13-05 — Query API + Query DSL + Saved Queries + DLQ Admin — SUMMARY

## Outcome

Shipped read-path for monitoring. Users can now query logs, metrics, and traces
through one JSON DSL that compiles to parameterised SQL against the existing
`v_monitoring_*` views. Saved queries sub-feature stores DSL bodies for reuse
by UI / alerts / MCP. Admin DLQ replay + `GET /health/monitoring` round out
the operator story.

## Files

### Created (15)

- `03_docs/00_main/08_decisions/029_monitoring_query_dsl.md` — ADR (see "Deviations").
- `03_docs/features/05_monitoring/05_sub_features/04_saved_queries/09_sql_migrations/02_in_progress/20260417_043_monitoring-saved-queries.sql` — applied → 01_migrated/.
- `backend/02_features/05_monitoring/query_dsl/__init__.py`
- `backend/02_features/05_monitoring/query_dsl/types.py`
- `backend/02_features/05_monitoring/query_dsl/validator.py`
- `backend/02_features/05_monitoring/query_dsl/compiler.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/__init__.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/schemas.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/repository.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/service.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/routes.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py` (health + DLQ)
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/__init__.py`
- `backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py`
- `backend/02_features/05_monitoring/sub_features/01_logs/nodes/query.py`
- `backend/02_features/05_monitoring/sub_features/02_metrics/nodes/query.py`
- `backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py`
- 7 new test modules (see Tests).

### Modified

- `backend/02_features/05_monitoring/feature.manifest.yaml` — added 4 query nodes (monitoring.logs.query, monitoring.metrics.query, monitoring.traces.query, monitoring.saved_queries.run) + new sub-feature `monitoring.saved_queries` (number 4) + 8 new routes.
- `backend/02_features/05_monitoring/routes.py` — include saved_queries router + admin router.
- `backend/02_features/05_monitoring/sub_features/01_logs/routes.py` — POST /v1/monitoring/logs/query.
- `backend/02_features/05_monitoring/sub_features/01_logs/service.py` — `query(conn, ctx, dsl)`.
- `backend/02_features/05_monitoring/sub_features/02_metrics/routes.py` — POST /v1/monitoring/metrics/query.
- `backend/02_features/05_monitoring/sub_features/02_metrics/service.py` — `query(conn, ctx, dsl)`.
- `backend/02_features/05_monitoring/sub_features/03_traces/routes.py` — POST query + GET /traces/{trace_id}.
- `backend/02_features/05_monitoring/sub_features/03_traces/service.py` — `query(...)` + `get_trace(...)`.
- `frontend/src/types/api.ts` — DSL types + SavedQuery + TraceSpanNode.
- `.paul/STATE.md` — 13-05 complete, 13-06 next.

## Migration

- **043** `20260417_043_monitoring-saved-queries.sql` — applied cleanly.
  Table `10_fct_monitoring_saved_queries` (VARCHAR(36) PK, JSONB dsl, partial
  unique on (org,owner,name) WHERE deleted_at IS NULL). View
  `v_monitoring_saved_queries` derives `is_deleted`.

## Tests

All green.

| File | Count |
|------|-------|
| `test_query_dsl.py` | 14 (unit: validator + compiler, no DB) |
| `test_logs_query_api.py` | 6 |
| `test_metrics_query_api.py` | 6 |
| `test_traces_query_api.py` | 4 |
| `test_saved_queries.py` | 7 |
| `test_monitoring_health.py` | 2 |
| `test_dlq_replay.py` | 2 |
| **New this plan** | **41** |
| **Full monitoring suite** | **120 / 120** (was 79 before) |

Pyright on new code + modified files: **0 errors, 0 warnings**.

## Smoke (live server, port 51734)

```text
GET  /health/monitoring
  → workers: logs_consumer / spans_consumer / apisix_scraper all running
  → nats.streams: MONITORING_DLQ, MONITORING_LOGS, MONITORING_SPANS
  → store.kind = "postgres", healthy = true

POST /v1/monitoring/metrics (register query.smoke.req counter) → 201
POST /v1/monitoring/metrics/query.smoke.req/increment (value=5) → 201
POST /v1/monitoring/metrics/query
     {target:metrics, metric_key:query.smoke.req, timerange:{last:1h},
      aggregate:sum, bucket:1m}
  → items: [{bucket_ts:"2026-04-17T08:51:00", value:5.0}]

POST /v1/monitoring/logs/query {timerange:{last:24h}, limit:3}
  → items: []  (no seeded logs in smoke org)

POST /v1/monitoring/saved-queries
     {name:"smoke errors", target:"logs",
      dsl:{target:"logs", severity_min:17, timerange:{last:"1h"}}}
  → 201 with full SavedQueryResponse (id, owner_user_id, shared=false, is_active=true)
```

## Deviations

1. **ADR-028 → ADR-029.** The plan asks for `028_monitoring_query_dsl.md`
   but `028_vault_foundation.md` already exists. New ADR is **029**; the body
   explicitly notes the renumbering. Nothing else references ADR-028 by
   number.
2. **Rollup-table selection deferred to 13-07.** Metrics compiler reads raw
   `evt_monitoring_metric_points`. 13-07 wires pg_cron to populate the
   rollup tables; the compiler swap-in point is documented in ADR-029 and in
   a comment at `compile_metrics_query`.
3. **Histogram percentile via `percentile_cont(value)` fallback.** Real
   bucket-summed histogram approximation needs the rollup tables and is
   noted as 13-07 follow-up.
4. **`rate` aggregate** is `(max - min) / bucket_seconds` — approximation;
   reset-aware rate follows rollups in 13-07.
5. **DLQ replay scope gate** uses `request.state.scopes` + dev header
   `x-monitoring-admin: 1` (full scope system lands later). Documented in
   the route docstring; tests assert 403 without the bypass.
6. **Admin + health routes** live in `sub_features/04_saved_queries/admin_routes.py`
   (module-local) to avoid spinning up a 5th sub-feature for two endpoints.
   Manifest registers them under the `monitoring.saved_queries` key.

## AC matrix

| AC | Status | Notes |
|----|--------|-------|
| AC-1 ADR published | ✅ | ADR-029 (see deviation #1) |
| AC-2 DSL shape | ✅ | Pydantic models in `types.py`; all 14 filter ops present |
| AC-3 Compiler + safety | ✅ | Zero f-string on user values (asserted in tests); field allowlist; org_id from ctx only; 90d cap; regex limiter |
| AC-4 Metrics rollup selection | ⚠️ | Deferred to 13-07 (see deviation #2); compiler uses raw table |
| AC-5 Endpoint envelopes | ✅ | All 7 endpoints return `{ok, data}`; cross-org returns empty rows (org filter isolates) |
| AC-6 Saved queries | ✅ | 6 endpoints; owner + shared visibility; run dispatches by target |
| AC-7 Worker health + DLQ | ✅ | `/health/monitoring` + `/v1/monitoring/dlq/replay` |
| AC-8 Nodes callable | ✅ | 4 request-kind nodes (logs.query, metrics.query, traces.query, saved_queries.run) |
| AC-9 Tests green | ✅ | 41 new, 120 total, all green |

## Readiness for 13-06 (UI)

- Frontend types in `frontend/src/types/api.ts` include `LogsQuery`,
  `MetricsQuery`, `TracesQuery`, `Filter`, `Timerange`, `SavedQuery`,
  `QueryResult<T>`, `LogRow`, `SpanRow`, `TimeseriesPoint`, `TraceSpanNode`.
- All query endpoints respect `x-org-id` / `x-workspace-id` headers, so the
  UI's existing auth middleware bridge works unchanged.
- Saved queries endpoint returns fully-typed rows ready for TanStack Query
  hooks under `frontend/src/features/monitoring/hooks/`.
- Trace detail endpoint returns flat spans ordered by `start_time_unix_nano`
  — client builds the `TraceSpanNode` tree via `parent_span_id`.
