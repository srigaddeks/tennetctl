# 13-08a SUMMARY — Alert rules + silences CRUD

Chunk A of Plan 13-08. Scope: schema + sub-feature scaffolding + CRUD + nodes + tests. No evaluator, no worker, no frontend.

## Migrations applied

- `20260417_049_monitoring-alert-rules.sql` — `01_dim_monitoring_alert_severity` (seeded info/warn/error/critical), `12_fct_monitoring_alert_rules`, `13_fct_monitoring_silences`, `20_dtl_monitoring_rule_state` (written by 13-08b evaluator), plus `v_monitoring_alert_rules` + `v_monitoring_silences`.
- `20260417_050_monitoring-alert-events.sql` — `60_evt_monitoring_alert_events` (partitioned by `started_at`, 3 days of partitions pre-created via `monitoring_ensure_partitions`), plus `v_monitoring_alert_events`.

Note: the alert events table is named `60_evt_monitoring_alert_events` to match the retention row pre-seeded in migration 045 (`alert_events` → `60_evt_monitoring_alert_events`, 90 days). The plan draft referenced `70_evt_…` but the pre-seeded retention row is the source of truth, so 60_ was used.

## Files created / modified

**Created (17):**
- 2 migrations (above)
- `backend/02_features/05_monitoring/sub_features/07_alerts/__init__.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/schemas.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/repository.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/service.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/routes.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/nodes/__init__.py`
- `…/nodes/rule_create.py`, `rule_update.py`, `rule_delete.py`, `rule_get.py`, `rule_list.py`, `silence_add.py`, `event_list.py`, `event_get.py`
- `tests/features/05_monitoring/test_alert_rules_crud.py`
- `tests/features/05_monitoring/test_silences_crud.py`

**Modified (3):**
- `backend/02_features/05_monitoring/routes.py` — include `07_alerts` router
- `backend/02_features/05_monitoring/feature.manifest.yaml` — new `monitoring.alerts` sub-feature with 8 nodes + 13 routes
- `backend/01_core/config.py` — added `monitoring_alert_evaluator_enabled` + `TENNETCTL_MONITORING_ALERT_EVALUATOR_ENABLED` (defaults to true; consumed by 13-08b)

## Endpoints (13)

- `GET/POST/GET/PATCH/DELETE /v1/monitoring/alert-rules[/{id}]`
- `POST /v1/monitoring/alert-rules/{id}/pause`
- `POST /v1/monitoring/alert-rules/{id}/unpause`
- `GET/POST /v1/monitoring/silences`, `DELETE /v1/monitoring/silences/{id}`
- `GET /v1/monitoring/alerts`, `GET /v1/monitoring/alerts/{id}`, `POST /v1/monitoring/alerts/{id}/silence`

## Nodes (8)

rule_create/update/delete (effect+audit), rule_get/list (request), silence_add (effect+audit), event_list/get (request). Evaluator node deferred to 13-08b.

## Tests

16 new tests, all green in isolation:
- `test_alert_rules_crud.py` — 11 tests (happy path, invalid DSL, invalid severity/target, duplicate-name, list, get, pause/unpause/update, soft-delete, cross-org 404, audit emit on create/update/delete)
- `test_silences_crud.py` — 5 tests (create, active-only list excludes expired, delete, inverted-window rejected, rule_id matcher)

Full monitoring suite: `167 passed` when run non-interleaved. 4 failures + 5 errors appear when the full suite runs in alphabetical order — these are **pre-existing** context-var fragility in `test_instrumentation.py`, `test_monitoring_health.py`, `test_notify_listener.py`, `test_dlq_replay.py` (global `_in_monitoring_bridge` ContextVar cannot survive multiple lifespans). Same tests fail when *any* early-alphabetic test that runs lifespan (e.g. `test_dashboards_crud.py`, `test_synthetic_checks.py`) precedes them. Not caused by this chunk.

## Smoke curl

Successful — `POST /v1/monitoring/alert-rules` returns 201 with full response envelope; `GET /v1/monitoring/alert-rules` returns the item.

## Pyright

```
0 errors, 0 warnings, 0 informations
```
(over `sub_features/07_alerts/` + both new test files)

## Deviations from plan draft

1. Alert events table uses prefix `60_evt_…` instead of `70_evt_…` to match the pre-seeded retention row from migration 045. Indices and view reference the `60_` name accordingly.
2. Severity seed is inlined in migration 049 rather than a separate YAML seed file — there are only 4 rows and they are never mutated, matching the inline-seed pattern used elsewhere (dim tables with tiny, immutable enums).
3. `notify_template_key` existence is NOT checked against notify templates in chunk A (plan says skip; 13-08b will validate before fan-out).

## Readiness for 13-08b

All evaluator dependencies are in place:
- `dtl_monitoring_rule_state.pending_fingerprints` exists for for-duration gating
- `evt_monitoring_alert_events` partitioned + indexed for fingerprint upserts
- `fct_monitoring_silences` with `v_monitoring_silences` view for match lookups
- `service.list_rules(..., is_active=True)` returns active rules for worker loops
- `config.monitoring_alert_evaluator_enabled` boot flag wired

13-08b can proceed directly to writing `evaluator.py` + `workers/alert_evaluator_worker.py` + the `monitoring.alerts.evaluate` node.
