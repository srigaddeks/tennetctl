---
phase: 13-monitoring
plan: 01
type: execute
status: complete
applied_at: 2026-04-17
---

# Plan 13-01 — APPLY SUMMARY

## Migrations applied (5)

All under `03_docs/features/05_monitoring/05_sub_features/*/09_sql_migrations/01_migrated/`:

| # | File | Sub-feature | Creates |
|---|------|-------------|---------|
| 037 | `20260417_037_monitoring-bootstrap.sql` | 00_bootstrap | schema + 4 dim + `fct_monitoring_resources` |
| 038 | `20260417_038_monitoring-logs.sql` | 01_logs | partitioned `evt_monitoring_logs` + 3 partitions + 4 indexes + `v_monitoring_logs` |
| 039 | `20260417_039_monitoring-metrics.sql` | 02_metrics | `fct_monitoring_metrics` (registry + histogram CHECK) + partitioned `evt_monitoring_metric_points` + 3 partitions + `v_monitoring_metrics` |
| 040 | `20260417_040_monitoring-traces.sql` | 03_traces | partitioned `evt_monitoring_spans` with `duration_ns` generated-stored + 3 partitions + `v_monitoring_spans` |
| 041 | `20260417_041_monitoring-resources-rollups.sql` | 00_bootstrap | 3 rollup parents (1m/5m/1h) × 3 partitions each + `v_monitoring_resources` |

**`\dt "05_monitoring".*`** reports 30 objects: 4 dim + 2 fct + 3 evt parents + 3 rollup parents + 3×3 evt partitions + 3×3 rollup partitions = 4 + 2 + 3 + 3 + 9 + 9 = 30. Matches AC-1 (verification step: ≥ 4 + 2 + 3 + 3 + 12 partitions + 4 views).

**Note on convention deviation from plan front-matter:** Plan YAML listed migration numbers 035-039; reconciliation bumped to 037-041 because notify plans 11-xx actually shipped 035 + 036 after the 13-01 plan was drafted. Migration numbers must be globally unique + monotonic.

## Seeds applied (5)

Under `03_docs/features/05_monitoring/05_sub_features/00_bootstrap/09_sql_migrations/seeds/`:

- `05monitoring_01_dim_severity.yaml` — 8 OTLP severity rows (id matches OTLP SeverityNumber)
- `05monitoring_02_dim_metric_kinds.yaml` — counter (1), gauge (2), histogram (3)
- `05monitoring_03_dim_span_kinds.yaml` — 6 OTLP SpanKind rows
- `05monitoring_04_dim_span_status.yaml` — unset (0), ok (1), error (2)
- `05monitoring_05_module_register.yaml` — re-asserts `01_catalog.01_dim_modules` id=4 monitoring (no-op on conflict; the catalog bootstrap seed already registered it)

## Store seam complete

`backend/02_features/05_monitoring/stores/`:
- `types.py` — 8 frozen dataclasses (LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery, ResourceRecord)
- 4 Protocol files — `logs_store.py`, `metrics_store.py`, `spans_store.py`, `resources_store.py`
- 4 Postgres implementations — `postgres_{logs,metrics,spans,resources}_store.py`
- `__init__.py` — 4 factories (`get_logs_store`, `get_metrics_store`, `get_spans_store`, `get_resources_store`) that read `TENNETCTL_MONITORING_STORE_KIND` (v0.1.5 accepts `postgres` only; other values raise `NotImplementedError` with forward-looking message).

`compute_resource_hash(service_name, instance_id, version, attrs)` uses SHA-256 over canonical JSON with sorted keys. Deterministic across attribute insertion order.

## JetStream bootstrap

- `backend/01_core/nats.py` — module-level singletons + `connect(url)` (3× backoff retry) + `close()` + `get_nats()/get_js()` + `_reset_for_tests()`.
- `backend/02_features/05_monitoring/bootstrap/jetstream.py` — creates **3** streams idempotently: `MONITORING_LOGS` (WorkQueue, 72h, 2GB, `monitoring.logs.otel.>`), `MONITORING_SPANS` (WorkQueue, 24h, 4GB, `monitoring.traces.otel.>`), `MONITORING_DLQ` (Limits, 7d, 1GB, `monitoring.dlq.>`). DLQ added proactively so 13-04 doesn't re-migrate.
- Lifespan (`backend/main.py`): `if "monitoring" in config.modules and config.monitoring_enabled: connect + bootstrap` wrapped in try/except → logs WARNING and continues when NATS unreachable. Shutdown calls `nats_core.close()` guarded by `_client is not None`.

## Config + deps

`backend/01_core/config.py`:
- Appended `monitoring` to `_DEFAULT_MODULES`
- Allowlist extended: `TENNETCTL_NATS_URL`, `TENNETCTL_MONITORING_ENABLED`, `TENNETCTL_MONITORING_STORE_KIND`
- `Config` frozen dataclass gained: `nats_url` (default `nats://localhost:4222`), `monitoring_enabled` (default `True`), `monitoring_store_kind` (default `"postgres"`)

`pyproject.toml` declares `nats-py>=2.9,<3.0` + `opentelemetry-proto>=1.28,<2.0`. Installed versions in venv: `nats-py 2.14.0`, `opentelemetry-proto 1.41.0`. Both import clean.

## Feature manifest

`backend/02_features/05_monitoring/feature.manifest.yaml` — matches `06_notify` shape exactly (`apiVersion: tennetctl/v1`, `kind: Feature`, metadata + spec). 3 sub-features declared with dotted keys (`monitoring.logs`, `monitoring.metrics`, `monitoring.traces`), all with empty `nodes: []` + `routes: []`.

No mirror to `03_docs/features/05_monitoring/feature.manifest.yaml` — notify does not mirror its manifest to docs either.

## Tests green

```
.venv/bin/pytest tests/features/05_monitoring/ -v
============================= 15 passed in 1.22s =============================
```

| File | Tests | Coverage |
|------|-------|----------|
| `test_stores.py` | 11 | Logs insert-batch + query (severity/trace_id/body_contains filter) + cursor pagination; Metrics register idempotent + counter increment + timeseries + gauge set/latest + histogram observe buckets + cardinality rejection; Spans insert + query_by_trace with duration_ns; Resources upsert idempotent + new-hash-new-row + hash determinism |
| `test_jetstream_bootstrap.py` | 4 | creates-when-missing + idempotent-when-present + config-update-path (mix) + graceful-connect-failure |

Test strategy: monitoring tests run against the LIVE DB (same pattern as `test_iam_orgs_api.py`, `test_audit_emit_node.py`) since the `05_monitoring` schema lives there. Local `db_conn` fixture cleans up all rows scoped to test `org_id`s in teardown.

## Backend boot confirmed

Full lifespan smoke (NATS running on 4222):
```
INFO:tennetctl.catalog:Catalog boot done: 6 features, 31 sub-features, 40 nodes, 0 deprecated
INFO:tennetctl.nats:NATS connected: nats://localhost:4222
INFO:tennetctl.monitoring.jetstream:jetstream stream created: MONITORING_LOGS
INFO:tennetctl.monitoring.jetstream:jetstream stream created: MONITORING_SPANS
INFO:tennetctl.monitoring.jetstream:jetstream stream created: MONITORING_DLQ
INFO:tennetctl:monitoring: jetstream streams MONITORING_LOGS + MONITORING_SPANS + MONITORING_DLQ ready
...
INFO:tennetctl:NATS connection closed.
```

Catalog upsert rows verified via psql:
- `01_catalog.10_fct_features` → includes `monitoring`
- `01_catalog.11_fct_sub_features` → includes `monitoring.logs`, `monitoring.metrics`, `monitoring.traces`

## Cross-import linter

`backend/01_catalog/linter.py → check_tree(".")` reports **0 violations** scoped to `backend/02_features/05_monitoring/`. Pre-existing violations in IAM sub-features are unchanged (not in 13-01 scope).

## Carve-outs recorded to STATE.md

Eight new rows appended to `.paul/STATE.md` Accumulated Context → Decisions table:

1. Monitoring `fct_*` tables are catalog/registry — exempt from pure-EAV
2. Monitoring `fct_*` use IDENTITY PKs (SMALLINT metrics, BIGINT resources) — not UUID v7
3. Monitoring `evt_*` use first-class OTel top-level columns, not pure-JSONB
4. `TIMESTAMP` (UTC) used on monitoring tables — override AC-1's `TIMESTAMPTZ`
5. Monitoring `fct_*` skip `is_test/created_by/updated_by` — no human actor on machine-emitted rows
6. Ingest-path nodes will skip `emit_audit` (hot-path audit bypass) — precedent in future 13-02/13-03
7. Monitoring NATS JetStream bootstrap is best-effort — WARNING + continue on failure
8. (existing in prior sessions) Every monitoring sub-feature is a full vertical per user directive — applies to 13-05/06 onward

## Deviations from plan

| Area | Plan | Reality | Reason |
|------|------|---------|--------|
| Migration numbers | 035-039 | **037-041** | 035/036 already shipped with notify after 13-01 plan was drafted |
| Resources table location | separate migration 039/041 | moved into **bootstrap migration 037** | logs + metrics + spans all FK `resource_id`, so resources must exist before those migrations in alphabetical-global order |
| TIMESTAMP vs TIMESTAMPTZ | AC-1 specified TIMESTAMPTZ | used **TIMESTAMP** (UTC) | project-wide convention in `.claude/rules/common/database.md` |
| DLQ stream | not in plan (slated for 13-04) | **added now** | prevents needless re-migration of stream configs in next plan |
| Test DB strategy | apply migrator against test DB | use **LIVE DB** with scoped org_id cleanup | matches existing integration-test pattern (test_iam_orgs_api.py, etc.); test DB doesn't auto-run feature migrations |
| `ResourcesStore.upsert` signature | `(conn, org_id, service_name, ...)` | `(conn, ResourceRecord)` | dataclass-based signature matches other stores' record-input pattern; hash still computed identically |

## Readiness

**13-02 + 13-03 may proceed.** Foundation is solid:
- Schema covers all three OTel pillars; no downstream migrations should need to alter existing columns
- Store seam in place — ingest code can depend on `get_*_store()` factories
- JetStream streams ready — consumers (13-04) can bind immediately
- Catalog registered `monitoring` feature with 3 empty sub-features awaiting node/route additions

**Known follow-ups:**
- `v_monitoring_resources` exists (Task 6); `v_monitoring_logs/_metrics/_spans` exist (Tasks 3-5). Total views = 4 → matches AC-1 verification.
- Rollup tables are empty shells; pg_cron wiring is 13-07.
- Ingest nodes + audit-bypass decision documented — 13-02/13-03 can use it.
