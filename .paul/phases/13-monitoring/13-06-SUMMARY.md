# Phase 13-06 — Consolidated Summary (13-06a + 13-06b + 13-06c)

**Date:** 2026-04-17
**Status:** COMPLETE — backend + frontend + E2E all green

---

## 13-06a — Backend: Dashboards + SSE Live Tail

### Migration
- `20260417_044_monitoring-dashboards.sql` — adds `10_fct_monitoring_dashboards`, `11_fct_monitoring_panels`, `v_monitoring_dashboards` (with `panel_count`), `v_monitoring_panels`.
- Cascade delete panels with parent. Partial UNIQUE on `(org_id, owner_user_id, name) WHERE deleted_at IS NULL`.

### Backend sub-feature (5 files)
- `backend/02_features/05_monitoring/sub_features/05_dashboards/` — full CRUD for dashboards + nested panels (POST/GET/PATCH/DELETE).
- SSE live-tail endpoint: `GET /v1/monitoring/logs/tail` — polls DB every 1s, heartbeats every 15s, org-scoped, filter-capable.
- 8 dashboard tests + 6 panel tests + 5 SSE tests = **19 pytest tests added** (total monitoring: 139).

---

## 13-06b — Frontend: Monitoring Pages

### Dependencies
- `recharts` ^3.8.1 — line charts for metrics
- `react-grid-layout` ^2.2.3 — resizable dashboard panels

### Pages (6)
- `/monitoring` — overview with links
- `/monitoring/logs` — Explorer + Live Tail tabs
- `/monitoring/metrics` — MetricPicker sidebar + MetricsChart + Add to Dashboard modal
- `/monitoring/traces` — traces list with filter
- `/monitoring/traces/[traceId]` — span waterfall
- `/monitoring/dashboards` — list + create modal
- `/monitoring/dashboards/[id]` — grid + edit mode + add panel modal

### Components (9)
TimerangePicker, DslFilterBuilder, MetricPicker, MetricsChart, LogExplorer, LogLiveTail, TraceWaterfall, DashboardGrid, Panel

### All interactive elements have `data-testid` attributes — confirmed by E2E suite.

---

## 13-06c — E2E: 4 Robot Framework suites

### Files
```
tests/e2e/monitoring/
├── monitoring_keywords.resource
├── 01_logs_explorer.robot   (5 tests)
├── 02_metrics_dashboard.robot (4 tests)
├── 03_traces_waterfall.robot  (4 tests)
└── 04_dashboards_crud.robot   (6 tests)
```

### Result: 19/19 tests PASS

### Defects found and fixed

**1. OTLP consumer org_id mismatch (critical)**

`LogsConsumer` and `SpansConsumer` in `workers/runner.py` hardcoded `org_id='tennetctl'`. In single-tenant mode, users get a UUID org_id from IAM. The query endpoints use session UUID — so the UI always returned 0 results.

Fix: `runner.py` now resolves the default org UUID from `v_orgs WHERE slug='default'` before instantiating consumers.

**2. OTLP trace IDs must be base64**

OTLP protobuf JSON format encodes `traceId`/`spanId` as base64 bytes. Hex strings were being mis-decoded to wrong-length IDs. Fixed in `monitoring_keywords.resource`.

**3. Strict-mode modal button collisions**

`text=Create` and `text=Add panel` matched both the modal heading and the button. Fixed with `xpath=//button[normalize-space(text())="Create"]`.

**4. Live tail timing**

Added wait for SSE "Connected" state (via `monitoring-livetail-pause` visibility) before pushing OTLP log to ensure SSE poll window includes the new event.

---

## Total test coverage (Phase 13)

| Layer | Tests | Status |
|-------|-------|--------|
| Backend pytest | 139 | Green |
| E2E Robot | 19 | Green |
| **Total** | **158** | **All green** |
