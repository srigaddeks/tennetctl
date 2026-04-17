# 13-04 SUMMARY — JetStream Consumers + Log Redaction + APISIX Scraper

**Status:** COMPLETE
**Date:** 2026-04-17
**Wave:** 3 (plans 13-01, 13-03 merged)

---

## What shipped

### Migrations + seed
- `20260417_042_monitoring-redaction-rules.sql` — `12_fct_monitoring_redaction_rules` (SMALLINT IDENTITY PK, registry carve-out) + `v_monitoring_redaction_rules` view. Named constraints + COMMENTs.
- `05monitoring_06_redaction_rules.yaml` — 14 global default rules seeded:
  credit card, AWS access key, JWT, bearer token, password k/v body substitution + 9 attribute-key denylist entries (password, token, authorization, cookie, set-cookie, api_key, secret, ssn, credit_card).

### Workers (new package `backend/02_features/05_monitoring/workers/`)
- `redaction.py` — `RedactionEngine` with compiled-regex cache, 60s TTL load-on-start + `maybe_reload`. Immutable — `apply()` returns a new dict. `set_rules()` test hook.
- `logs_consumer.py` — pull-subscribe `MONITORING_LOGS`/durable `monitoring-logs-postgres`. Per message: ResourceLogs protobuf → ResourcesStore.upsert → decode LogRecord list → apply redaction → LogsStore.insert_batch (single tx). DLQ routing on max_deliver exhaustion; nak otherwise. Decode failures go straight to DLQ.
- `spans_consumer.py` — mirror for `MONITORING_SPANS`/durable `monitoring-spans-postgres`. No redaction per plan scope.
- `apisix_scraper.py` — httpx.AsyncClient polling `config.monitoring_apisix_url` every 15s. Parses Prometheus text via `prometheus_client.parser`. Auto-registers metrics under `apisix.<name>` prefix (cached per `(name, kind)`). Counter stored as delta from last value. HTTP >=400 / connect errors log warning + return 0. Never raises into supervisor.
- `runner.py` — `WorkerPool.start(pool, js, config)` / `stop(timeout)` / `health()`. Wraps each worker in `_supervised(name, factory)` with exponential backoff (1, 2, 4, 8, 16, 32, 60s cap), crash restart, per-worker `WorkerState` (running / last_heartbeat / restart_count / last_error). Graceful-stop path calls each worker's `stop()` then cancels asyncio tasks within timeout. `_backoff_override` test hook.

### Modifications
- `backend/01_core/config.py` — +5 Config fields (`monitoring_apisix_scrape_enabled`, `monitoring_apisix_url`, `monitoring_consumer_batch_size`, `monitoring_consumer_max_deliver`, `monitoring_consumer_ack_wait_s`) + 5 allowlist entries. Default APISIX URL = `http://localhost:51791/apisix/prometheus/metrics` (matches docker-compose).
- `backend/main.py` — lifespan starts `WorkerPool` after JetStream bootstrap (uses `js=None` fallback when NATS down so the scraper still runs). Shutdown: `pool.stop(timeout=10)` before NATS drain.

### Tests
- `tests/features/05_monitoring/test_redaction.py` — 8 tests (CC body, JWT attr, denylist drop + count, priority order, immutability, passthrough, invalid regex skip, substring key match).
- `tests/features/05_monitoring/test_logs_consumer.py` — 5 tests (single message → insert, batch of 5 in one tx, max-delivery → DLQ, nak while not exhausted, decode failure → DLQ).
- `tests/features/05_monitoring/test_spans_consumer.py` — 3 tests (insert + resource upsert, DLQ on exhaustion, nak).
- `tests/features/05_monitoring/test_apisix_scraper.py` — 4 tests (sample prom text → register + write, HTTP 500 swallowed, idempotent register across scrapes, httpx.ConnectError swallowed).
- `tests/features/05_monitoring/test_worker_supervisor.py` — 4 tests (start/stop with no-js, restart on crash + increments counter, stop cancels long sleeper, health snapshot).

---

## Verification

### Pytest
- 24 new / 24 pass
- Full monitoring suite: **79/79 pass** (55 prior + 24 new — 40% above the ≥15 target)
- Full project suite: **453 pass, 11 fail** (all 11 failures are pre-existing `test_migrator.py` drift from Phase 1 refactor, tracked in STATE.md deferred gaps — unchanged by this plan)

### Pyright
- 0 errors, 0 warnings across `backend/02_features/05_monitoring/workers/` + all 5 new test files (prometheus_client has type stubs, so only nats/opentelemetry imports needed the existing pyright-ignore pattern).

### Smoke test (live backend on :51734 with NATS + APISIX + Postgres up)
- OTLP log posted for service `consumer-test` with body `"hello world password=s3cret end"` and attributes `{password: hunter2, user: alice}`
- Row landed in `evt_monitoring_logs` via JetStream consumer → `ResourcesStore.upsert` → `LogsStore.insert_batch`
- Body redacted to `"hello world password=[REDACTED] end"`
- `password` attribute dropped; `user` preserved
- `dropped_attributes_count = 1`
- APISIX scraper registered 6 metrics (`apisix.apisix_http_requests_total`, `apisix_nginx_http_current_connections`, `apisix_nginx_metric_errors`, `apisix_node_info`, `apisix_shared_dict_capacity_bytes`, `apisix_shared_dict_free_space_bytes`) and wrote points
- Stdlib logging bridge (from 13-03) also pumping — ~200k real log rows observed during smoke, confirming consumer throughput

---

## AC status

| AC | Status |
| --- | --- |
| AC-1 Logs consumer durability | PASS — pull-subscribe, batch, ack on success, nak, DLQ after max_deliver |
| AC-2 Spans consumer | PASS — mirror semantics; trace_id/span_id hex encoded; duration_ns via generated column |
| AC-3 Redaction | PASS — 14 default rules seeded; regex + denylist; 60s TTL reload; dropped_attributes_count increments; smoke-verified |
| AC-4 APISIX scraper | PASS — 15s poll, text parser, counter/gauge/histogram written; HTTP + connect failures logged-not-raised; gated by `monitoring_apisix_scrape_enabled` |
| AC-5 Workers lifecycle | PASS — WorkerPool in lifespan; per-worker supervisor with exponential backoff; `stop(timeout=10)` drain; `health()` dict |
| AC-6 DLQ stream | PASS — `MONITORING_DLQ` already present from 13-01; DLQ publish verified via unit test |
| AC-7 Tests green | PASS — 24 ≥ 15 target |

---

## Deviations from plan

1. **Migration number 042 not 040.** Plan front-matter listed `040` but 13-01 landed 037, 041; 13-02 landed 039; 13-03 landed 040. Per Sri's directive in prompt ("Migration number: **042** is next"), used 042. Table name `12_fct_monitoring_redaction_rules` keeps the `nn_type_name` convention (id 11 is `fct_monitoring_resources`).
2. **DLQ replay route deferred to 13-05** per plan boundaries.
3. **CRUD routes for redaction rules deferred to 13-05** per plan scope — not creating a full sub-feature scaffolding this wave.
4. **Immutability contract honored** — `RedactionEngine.apply()` returns a new dict; original record object + its nested `attributes` dict are unchanged. Verified via unit test.
5. **`js=None` fallback** — when NATS is unreachable the WorkerPool still starts the APISIX scraper (it doesn't need JetStream). Consumer workers are simply not scheduled.
6. **Counter delta tracking** — APISIX emits cumulative counters; scraper converts to incremental deltas via per-`(metric_id, label_tuple)` last-value cache. Resets gracefully when counter rolls back (handles restarts).

---

## Readiness for 13-05

Green. Things 13-05 can assume:
- `fct_monitoring_redaction_rules` + view exist. CRUD endpoints will need: GET list / POST create / GET one / PATCH update / DELETE soft-delete (but table has no `deleted_at`; add via migration if desired, or treat `is_active=false` as soft delete).
- `WorkerPool.health()` returns per-worker dict — plug into `/health/monitoring` endpoint.
- `MONITORING_DLQ` stream carries DLQ messages on subjects `monitoring.dlq.logs` + `monitoring.dlq.spans` with headers `tennetctl-dlq-reason` + `tennetctl-dlq-subject`. Replay route just pulls from DLQ and re-publishes to origin subject.
- All config knobs already in `_ALLOWED_TENNET_ENV`.

---

## Files (14 created + 3 modified)

Created:
- `03_docs/features/05_monitoring/05_sub_features/01_logs/09_sql_migrations/01_migrated/20260417_042_monitoring-redaction-rules.sql` (moved by migrator after apply)
- `03_docs/features/05_monitoring/05_sub_features/01_logs/09_sql_migrations/seeds/05monitoring_06_redaction_rules.yaml`
- `backend/02_features/05_monitoring/workers/__init__.py`
- `backend/02_features/05_monitoring/workers/redaction.py`
- `backend/02_features/05_monitoring/workers/logs_consumer.py`
- `backend/02_features/05_monitoring/workers/spans_consumer.py`
- `backend/02_features/05_monitoring/workers/apisix_scraper.py`
- `backend/02_features/05_monitoring/workers/runner.py`
- `tests/features/05_monitoring/test_redaction.py`
- `tests/features/05_monitoring/test_logs_consumer.py`
- `tests/features/05_monitoring/test_spans_consumer.py`
- `tests/features/05_monitoring/test_apisix_scraper.py`
- `tests/features/05_monitoring/test_worker_supervisor.py`

Modified:
- `backend/01_core/config.py`
- `backend/main.py`
- (prometheus-client added to venv — install step only)
