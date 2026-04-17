# 13-06c Summary — Monitoring E2E Tests

**Date:** 2026-04-17
**Status:** COMPLETE — 19/19 tests green

---

## What was built

4 Robot Framework E2E suites + 1 shared keywords resource for the monitoring feature.

### Files created

```
tests/e2e/monitoring/
├── monitoring_keywords.resource       — shared seeding + API keywords
├── 01_logs_explorer.robot             — 5 tests
├── 02_metrics_dashboard.robot         — 4 tests
├── 03_traces_waterfall.robot          — 4 tests
└── 04_dashboards_crud.robot           — 6 tests
```

### Test run result

```
Monitoring E2E     19 tests, 19 passed, 0 failed
```

---

## Suite breakdown

### 01_logs_explorer.robot (5 tests)

Tests: logs explorer renders seeded rows, INFO severity filter, ERROR severity filter, live tail tab reachable, live tail streams new log entry.

Key data-testids used:
- `monitoring-log-explorer`
- `monitoring-logs-tab-live` / `monitoring-logs-tab-explorer`
- `monitoring-log-body-search`
- `monitoring-log-sev-info` / `monitoring-log-sev-error`
- `monitoring-log-row-{id}` (dynamic)
- `monitoring-log-live-tail`
- `monitoring-livetail-pause` / `monitoring-livetail-resume` / `monitoring-livetail-clear`

### 02_metrics_dashboard.robot (4 tests)

Tests: metric picker renders, selecting a metric shows chart, bucket toggle re-renders chart, "Add to dashboard" creates panel on a new dashboard.

Key data-testids used:
- `monitoring-metric-picker`
- `monitoring-metric-search`
- `monitoring-metric-{key}` (dynamic)
- `monitoring-metrics-chart`
- `monitoring-metrics-bucket`
- `monitoring-metrics-add-to-dash`

### 03_traces_waterfall.robot (4 tests)

Tests: traces list renders, trace row links to waterfall, waterfall shows parent+child spans, direct URL navigation.

Key data-testids used:
- `heading-monitoring-traces`
- `monitoring-traces-service`
- `monitoring-trace-row-{trace_id}` (dynamic)
- `monitoring-trace-waterfall`
- `monitoring-trace-span-{span_id}` (dynamic)
- `heading-monitoring-trace`

### 04_dashboards_crud.robot (6 tests)

Tests: create dashboard modal, card appears in list, open detail page, add panel, panel persists after reload, delete dashboard.

Key data-testids used:
- `monitoring-dashboard-new`
- `monitoring-dashboard-name`
- `monitoring-dashboard-card-{id}` (dynamic)
- `monitoring-dashboard-add-panel`
- `monitoring-dashboard-grid`
- `monitoring-panel-title`
- `monitoring-panel-{id}` (dynamic)
- `monitoring-dashboard-delete-{id}` (dynamic)
- `heading-monitoring-dashboard`

---

## Defects surfaced and fixed

### Critical: OTLP consumer org_id mismatch (backend fix)

**File:** `backend/02_features/05_monitoring/workers/runner.py`

**Problem:** The `LogsConsumer` and `SpansConsumer` were instantiated with `org_id='tennetctl'` (hardcoded). In single-tenant mode, user sessions have org_id as a UUID (`019d9660-...`). The monitoring query endpoints use the session's UUID org_id — so UI queries always returned empty results even though the DB had 300k+ log records.

**Fix:** In `runner.py`, added logic to resolve the default org UUID from the IAM DB before instantiating the consumers. When `TENNETCTL_SINGLE_TENANT=true`, the runner queries `v_orgs` for slug `"default"` and passes that UUID as `org_id` to both `LogsConsumer` and `SpansConsumer`.

This is a clear scaffolding error: the consumer and query sides used different org_id representations.

### OTLP trace IDs must be base64 in JSON format

**Problem:** Initial trace seeding used hex-string `traceId`/`spanId` in OTLP JSON payload. The protobuf JSON format requires base64-encoded bytes for these fields. Hex was being decoded as base64, producing garbled 47-char trace_ids in the DB.

**Fix:** Updated `Post OTLP Parent Child Trace` keyword to generate hex IDs, base64-encode them for the JSON payload, and return the hex form for UI assertions.

### Strict-mode locator collisions in modals

**Problem:** `Click    text=Create` and `Click    text=Add panel` resolved to multiple elements (modal heading + button). Robot Browser library raises `strict mode violation` when a locator matches more than one element.

**Fix:** Changed to `xpath=//button[normalize-space(text())="Create"]` and `xpath=//button[normalize-space(text())="Add panel"]` which precisely targets the button element.

### Live tail timing

**Problem:** Live tail test was checking for `text=LIVETAIL-MARKER-{suite_ts}` but in the full suite run the marker text hadn't appeared within 20s. Root cause: the marker from seeding needed to wait for the "Connected" SSE status before being pushed.

**Fix:** Added explicit wait for `[data-testid="monitoring-livetail-pause"]` (indicates active connection) + 2s settle time + fresh epoch timestamp per-test run (not reusing suite setup `${TS}`).

---

## Artifacts

- `artifacts/13_monitoring_e2e/log.html`
- `artifacts/13_monitoring_e2e/report.html`
- `artifacts/13_monitoring_e2e/output.xml`

---

## Readiness for 13-07

All monitoring E2E flows verified green:
- OTLP pipeline (logs + traces) end-to-end via browser
- Metrics picker + chart rendering
- Dashboard CRUD including panel creation and persistence
- Live tail SSE streaming

The org_id fix is required for any monitoring data to appear in production single-tenant deployments. This should be committed with the E2E suites.
