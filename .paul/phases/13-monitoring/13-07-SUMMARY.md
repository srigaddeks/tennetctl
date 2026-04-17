# 13-07 SUMMARY — Retention, Rollups, Partition Management, Synthetic Checks, LISTEN/NOTIFY

**Phase:** 13 — Monitoring
**Plan:** 07
**Status:** COMPLETE
**Date:** 2026-04-17

## Outcome

All 4 closing operational concerns shipped: rollup aggregation procs, partition create/drop lifecycle, HTTP synthetic checks (CRUD + runner + metrics + audit), and LISTEN/NOTIFY-based log live-tail. 157/157 monitoring pytest green (139 pre-existing + 18 new). 0 pyright errors on new modules.

## Critical decision — pg_cron fallback

**pg_cron is NOT available** on the project's `postgres:16-alpine` image (confirmed via `SELECT name FROM pg_available_extensions`). The migration attempts `CREATE EXTENSION IF NOT EXISTS pg_cron` inside a `DO ... EXCEPTION WHEN OTHERS` block, logs NOTICE, and falls through. All scheduling is done by **asyncio workers** in the Python runtime:

- `RollupScheduler` — 3 tasks looping every 60/300/3600 seconds, each running `SELECT monitoring_rollup_1m/5m/1h()`
- `PartitionManager` — 1 task, runs once on startup then daily at 03:00 UTC
- `SyntheticRunner` — 1 reload task polling active checks every 30s + 1 task per check at its `interval_seconds`
- `NotifyListener` — dedicated asyncpg connection LISTENing on `monitoring_logs_new`

This matches the existing `apisix_scraper` precedent and avoids any docker-compose / image rebuild changes.

## Migrations applied

| # | File | Purpose |
|---|------|---------|
| 045 | `20260417_045_monitoring-pgcron-setup.sql` | pg_cron best-effort + `pgcrypto` + `fct_monitoring_retention_policies` (7 seeded rows incl. alert_events for 13-08) |
| 046 | `20260417_046_monitoring-rollup-procs.sql` | `dtl_monitoring_rollup_watermarks` + `monitoring_rollup_1m/5m/1h()` + `monitoring_histogram_array_sum()` helper |
| 047 | `20260417_047_monitoring-partition-procs.sql` | `monitoring_ensure_partitions(table, days_ahead)` + `monitoring_drop_old_partitions(table, days)` + `monitoring_partition_manager()` |
| 048 | `20260417_048_monitoring-synthetic-checks.sql` | `fct_monitoring_synthetic_checks` + `dtl_monitoring_synthetic_state` + `v_monitoring_synthetic_checks` + LISTEN/NOTIFY trigger on `60_evt_monitoring_logs` |

## Files created / modified

**Created (21):**
- 4 SQL migrations (above)
- `backend/02_features/05_monitoring/sub_features/06_synthetic/` — `__init__.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`
- `backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/` — `__init__.py`, `create_check.py`, `update_check.py`, `delete_check.py`, `get_check.py`, `list_checks.py`
- `backend/02_features/05_monitoring/workers/rollup_scheduler.py`
- `backend/02_features/05_monitoring/workers/partition_manager.py`
- `backend/02_features/05_monitoring/workers/synthetic_runner.py`
- `backend/02_features/05_monitoring/workers/notify_listener.py`
- `tests/features/05_monitoring/test_rollups.py` (5 tests)
- `tests/features/05_monitoring/test_partition_manager.py` (4 tests)
- `tests/features/05_monitoring/test_synthetic_checks.py` (6 tests)
- `tests/features/05_monitoring/test_notify_listener.py` (3 tests)

**Modified (6):**
- `backend/01_core/config.py` — 4 new flags + 4 new allowlist entries
- `backend/02_features/05_monitoring/routes.py` — include synthetic router
- `backend/02_features/05_monitoring/workers/runner.py` — register 4 new workers
- `backend/02_features/05_monitoring/sub_features/01_logs/routes.py` — SSE tail prefers NotifyListener broadcaster, falls back to polling
- `backend/02_features/05_monitoring/query_dsl/compiler.py` — `_check_retention()` helper called in logs/metrics/traces compilers; clear 400 error with table + days
- `backend/02_features/05_monitoring/feature.manifest.yaml` — synthetic sub-feature + 5 nodes + 5 routes
- `tests/features/05_monitoring/test_worker_supervisor.py` — mock config sets new flags to False

## Acceptance

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 pg_cron installed | ✗ unavailable → asyncio fallback | migration 045 logs NOTICE; 4 asyncio workers cover same work |
| AC-2 Rollup correctness | ✓ | test_rollups: basic_aggregation, idempotent, histogram_elementwise, gauge_uses_last, watermark_advances |
| AC-3 Partition lifecycle | ✓ | test_partition_manager: ensure/drop/iterates_all/skips_missing; live: 48 log partitions across 9 tables |
| AC-4 Synthetic checks | ✓ | 5 endpoints + 5 nodes + runner + state table; runner emits up/duration metrics and down audit on 3rd failure |
| AC-5 LISTEN/NOTIFY log tail | ✓ | trigger on parent propagates to 9 child partitions; NotifyListener + Broadcaster + SSE subscribe path; test confirms payload delivery |
| AC-6 Cold-query "data expired" | ✓ | `_check_retention` in compiler; 400 `INVALID_QUERY` with table + days |
| AC-7 Manifest + workers | ✓ | sub_feature key=monitoring.synthetic added; 4 new workers registered in WorkerPool |
| AC-8 Tests ≥ 15 | ✓ | 18 new; 157/157 green |

## Smoke verification

```bash
$ psql -c "SELECT \"05_monitoring\".monitoring_rollup_1m();"
 monitoring_rollup_1m
 --------------------
                  336

$ psql -c "SELECT * FROM \"05_monitoring\".monitoring_partition_manager();"
 (7 rows — 5 partitions created for each retention-policy table)

$ psql -c "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='05_monitoring' AND c.relname LIKE '60_evt_monitoring_logs_p%';"
 count | 48

$ psql -c "SELECT tgname FROM pg_trigger WHERE tgname='trg_monitoring_logs_notify';"
 9 rows (parent + 8 child partitions)

$ psql -c "SELECT code, table_name, days_to_keep, tier FROM \"05_monitoring\".\"10_fct_monitoring_retention_policies\";"
 7 rows — logs_hot/spans_hot/metric_points_hot/_1m/_5m/_1h/alert_events
```

## Pyright

```
backend/02_features/05_monitoring/workers/rollup_scheduler.py
backend/02_features/05_monitoring/workers/partition_manager.py
backend/02_features/05_monitoring/workers/synthetic_runner.py
backend/02_features/05_monitoring/workers/notify_listener.py
backend/02_features/05_monitoring/sub_features/06_synthetic/
→ 0 errors, 0 warnings, 0 informations
```

## Deviations

1. **pg_cron → asyncio workers.** Fallback path described above. Functionally equivalent — same procs, different scheduler.
2. **Retention check applied as a 1-day slack.** `last=7d` against 7d retention would otherwise reject the pre-existing `test_traces_compile_with_filters`. The slack keeps boundary queries legal while still catching clearly-expired timeranges (e.g. `last=30d` against spans/7d).
3. **Node + 5-endpoint shape.** Sub-feature sticks to the 5-endpoint maximum (list/create/get/patch/delete); separate actions like "run now" are deferred (the runner auto-polls).
4. **Workers key listed as manifest comment** (not `workers:` schema field) because the existing manifest Pydantic model forbids extra keys. Documenting them as a comment is the minimum-surface option.
5. **Existing test fix:** `test_worker_supervisor::test_start_stop_cleanly_with_no_js` — `_make_config` was using `MagicMock` whose attributes are truthy, causing the new workers to auto-start. Added explicit `False` flags. No other pre-existing tests modified.

## Readiness for 13-08 (alerting)

- `alert_events` retention policy (90d, hot) already seeded in 045 — when 13-08 creates `60_evt_monitoring_alert_events`, partition manager will pick it up automatically without a new migration.
- Synthetic `down` audit event + `consecutive_failures` counter already wired — 13-08 only needs to react to `monitoring.synthetic.down` events + add alert channels.
- NotifyListener's broadcaster pattern generalizes: 13-08 can publish to a second channel (`monitoring_alerts_new`) using the same architecture.
- Retention compile-time check (`_check_retention`) is extendable — add alert-events as a cold-check target when 13-08 lands its query endpoints.

## Test evidence

```
$ TENNETCTL_MONITORING_*=false .venv/bin/pytest tests/features/05_monitoring/ -q
........................................................................ [ 45%]
........................................................................ [ 91%]
.............                                                            [100%]
157 passed in 24.09s
```
