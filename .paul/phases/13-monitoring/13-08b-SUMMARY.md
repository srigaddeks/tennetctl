# 13-08b — Alert Evaluator + Worker + Notify Integration — SUMMARY

## Scope delivered

- `evaluator.py` — pure logic module: DSL compile + condition check + for_duration gating + fingerprint dedup + resolve detection + state persistence
- `alert_evaluator_worker.py` — periodic loop over active rules (30s default), applies transitions under per-rule transactions, drives notify
- `runner.py` — registers `AlertEvaluatorWorker` as the 9th supervised worker (gated on `monitoring_alert_evaluator_enabled`)
- `service.py` extensions:
  - `insert_alert_event`, `update_alert_event`, `find_firing_event`
  - `find_matching_silences` — matcher shape `{rule_id?, labels?}`, empty matcher matches nothing
  - `update_rule_state` — upsert last_eval_at/duration/error
  - `evaluate_all_active_rules(pool, ctx_factory)` orchestrator
- `nodes/evaluate.py` — `monitoring.alerts.evaluate` effect node (`tx: own`, 15s timeout) — manifest updated
- Config: `monitoring_alert_eval_interval_s` (default 30), `monitoring_alert_notify_throttle_minutes` (default 15), env vars added to allowlist

## Files

Created:
- `backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py`
- `backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py`
- `backend/02_features/05_monitoring/workers/alert_evaluator_worker.py`
- `tests/features/05_monitoring/test_alert_evaluator.py` (9 tests)
- `tests/features/05_monitoring/test_alert_notify_integration.py` (5 tests)
- `tests/features/05_monitoring/test_silences_match.py` (5 tests)
- `tests/features/05_monitoring/test_alert_events_api.py` (3 tests)
- `.paul/phases/13-monitoring/13-08b-SUMMARY.md`

Modified:
- `backend/02_features/05_monitoring/sub_features/07_alerts/service.py`
- `backend/02_features/05_monitoring/workers/runner.py`
- `backend/02_features/05_monitoring/feature.manifest.yaml`
- `backend/01_core/config.py`
- `tests/features/05_monitoring/test_worker_supervisor.py` (add `monitoring_alert_evaluator_enabled=False` to MagicMock)

## Test results

- New tests (evaluator + notify + silences + events API): **22 passed**
- Full monitoring suite: **194 passed, 3 pre-existing teardown errors** (dlq_replay, monitoring_health, notify_listener — all errors are in teardown, tests themselves PASS; caused by monitoring instrumentation's context-var reset on shutdown — unrelated to this chunk)
- Pyright: **0 errors, 0 warnings** across all modified/new files

## Smoke test

```
ORG=...; USER=...
# register metric + record a value
POST /v1/monitoring/metrics      body: {"key":"alerts.smoke","kind":"counter","label_keys":[]}
POST /v1/monitoring/metrics/alerts.smoke/increment body: {"value":10}
# create rule
POST /v1/monitoring/alert-rules  body: { ..., "condition": {"op":"gt","threshold":0,"for_duration_seconds":0}, "dsl": {..., "timerange": {"last":"15m"}} }
# wait one eval cycle
sleep 25
GET /v1/monitoring/alerts?state=firing
```

Result: firing event present with `value=10, threshold=0, state=firing, silenced=false`. Health endpoint shows `alert_evaluator` running with recent heartbeat.

DSL `timerange.last` must be one of the Pydantic-enum values (`15m / 1h / 24h / 7d / 30d / 90d`). Using `5m` returns 400 INVALID_DSL — documented for chunk C UI.

## Design notes

- **Evaluation window** = `max(for_duration_s, rule.timerange.last_s, 60s)` — the evaluator query runs over a window big enough to observe the condition AND the for_duration gate. Overriding the rule's `timerange` with a smaller window was a bug — fixed.
- **Fingerprint** = `sha256(rule_id || sorted-json(labels))` — deterministic across restarts; enables safe idempotent inserts into `60_evt_monitoring_alert_events` (PK `(id, started_at)`), collision check via `find_firing_event`.
- **Pending state** lives in `20_dtl_monitoring_rule_state.pending_fingerprints` — a JSON map `{fingerprint: first_breach_iso}` — consulted + updated per eval cycle; cleared when the fingerprint graduates to firing or resolves.
- **Silence matching** — active + non-expired silences with matcher `{rule_id}` or `{labels}` or both; empty matcher intentionally matches nothing (per migration comment).
- **Throttle** — `last_notified_at > (now - throttle_s)` suppresses both repeat firing notifies and the resolve notify within the same window.
- **Recipient resolution (v0.1)** — `rule.labels["recipient_user_id"]` only. No recipient = skip notify + log warning + bump `monitoring.alerts.notify_skipped_no_recipient_total` counter. A richer resolver (vault default key, on-call rotations, group membership) is **deferred to v0.2**.
- **org_id coercion** — alert_rules.org_id is `UUID`, metric_points.org_id is `VARCHAR(36)`. The worker coerces `rule["org_id"]` to `str` when building the NodeContext to avoid asyncpg type mismatch in the DSL-compiled query. This is a schema-inconsistency workaround; a harmonization migration is v0.2 scope.
- **Self-metrics** emitted via the monitoring SDK: `monitoring.alerts.evaluations_total` (counter), `monitoring.alerts.rules_active` (gauge, sample per cycle), `monitoring.alerts.notify_failures_total`, `monitoring.alerts.notify_skipped_no_recipient_total`. All emit attempts are wrapped in try/except so metric failures never break evaluation.

## Deviations

- No audit emission on transitions (the evaluate node is declared `emits_audit: true`, but audit emission happens through `notify.send.transactional` which has its own audit). A dedicated `monitoring.alerts.fired` / `monitoring.alerts.resolved` audit hook can be layered in v0.2.
- Rule state upsert preserves existing `pending_fingerprints` when the worker calls `update_rule_state` for last_eval_at bookkeeping (the evaluator already wrote the canonical pending map in the same txn).
- Testing strategy: evaluator tests monkey-patch `query_dsl.compile/validate` to return canned observation SQL (UNION ALL VALUES) so evaluator logic can be tested without invoking real metric inserts. Notify/silence tests mock `catalog.run_node` at the worker level.

## Readiness for 13-08c

Backend is feature-complete for the frontend to:
- list firing alerts (`GET /v1/monitoring/alerts?state=firing`) — verified green
- list all events with state/severity/since filters — verified green
- get alert detail by `(id, started_at)` — verified green
- CRUD rules + silences — (13-08a)

Frontend should surface the recipient-resolution limitation (a UI affordance to set `labels.recipient_user_id` per rule). A proper "notify target" field on the rule is a v0.2 schema change.
