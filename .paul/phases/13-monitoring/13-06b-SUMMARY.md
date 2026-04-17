# Phase 13-06b — Monitoring Frontend Summary

Scope: frontend for Plan 13-06 (backend complete in 13-06a). Robot E2E deferred to 13-06c.

## Dependencies installed

- `recharts` ^3.8.1
- `react-grid-layout` ^2.2.3 (v2 API — different from legacy typings)
- `@types/react-grid-layout` ^1.3.6 (kept for reference but the package now ships its own types that supersede it)

## Files created / modified

### Types (1)
- `frontend/src/types/api.ts` — added `Dashboard`, `DashboardDetail`, `DashboardListResponse`, `DashboardCreateRequest`, `DashboardUpdateRequest`, `Panel`, `PanelType`, `GridPos`, `PanelCreateRequest`, `PanelUpdateRequest`, `TraceDetailResponse`, `SavedQueryListResponse`. Existing monitoring types (`Metric*`, `LogsQuery`, `MetricsQuery`, `TracesQuery`, `Filter`, `Timerange`, `LogRow`, `SpanRow`, `TimeseriesPoint`, `QueryResult`) were already present.

### Hooks (6)
- `frontend/src/features/monitoring/hooks/use-metrics-list.ts`
- `frontend/src/features/monitoring/hooks/use-metrics-query.ts`
- `frontend/src/features/monitoring/hooks/use-logs-query.ts`
- `frontend/src/features/monitoring/hooks/use-traces-query.ts`
- `frontend/src/features/monitoring/hooks/use-dashboards.ts`
- `frontend/src/features/monitoring/hooks/use-live-tail.ts`

### Components (9)
- `frontend/src/features/monitoring/_components/timerange-picker.tsx`
- `frontend/src/features/monitoring/_components/dsl-filter-builder.tsx`
- `frontend/src/features/monitoring/_components/metric-picker.tsx`
- `frontend/src/features/monitoring/_components/metrics-chart.tsx`
- `frontend/src/features/monitoring/_components/log-explorer.tsx`
- `frontend/src/features/monitoring/_components/log-live-tail.tsx`
- `frontend/src/features/monitoring/_components/trace-waterfall.tsx`
- `frontend/src/features/monitoring/_components/panel.tsx`
- `frontend/src/features/monitoring/_components/dashboard-grid.tsx`

### Pages (7)
- `frontend/src/app/(dashboard)/monitoring/page.tsx` — overview
- `frontend/src/app/(dashboard)/monitoring/logs/page.tsx` — explorer + live tail tabs
- `frontend/src/app/(dashboard)/monitoring/metrics/page.tsx` — picker + chart + add-to-dashboard modal
- `frontend/src/app/(dashboard)/monitoring/traces/page.tsx` — list with filters
- `frontend/src/app/(dashboard)/monitoring/traces/[traceId]/page.tsx` — waterfall
- `frontend/src/app/(dashboard)/monitoring/dashboards/page.tsx` — card grid
- `frontend/src/app/(dashboard)/monitoring/dashboards/[id]/page.tsx` — edit/save layout, add panel

### Nav (1)
- `frontend/src/config/features.ts` — added Monitoring feature group with sub-links (Overview, Logs, Metrics, Traces, Dashboards). Sidebar reads this automatically.

## Verification

- `npx tsc --noEmit` → 0 errors.
- `npm run build` → success; 37 routes generated, 5 monitoring routes prerendered (`/monitoring`, `/monitoring/logs`, `/monitoring/metrics`, `/monitoring/traces`, `/monitoring/dashboards`) + 2 dynamic (`/monitoring/dashboards/[id]`, `/monitoring/traces/[traceId]`).
- `npm run lint` → 0 new errors in monitoring files. Pre-existing vault and notify lint issues are untouched.

## Notes

- `react-grid-layout` v2 has a very different API from its legacy `@types` package. No `WidthProvider` HOC — the new API uses `useContainerWidth()` hook + requires explicit `width` prop on `ResponsiveGridLayout`. Drag/resize are controlled via `dragConfig` / `resizeConfig` props, not top-level `isDraggable`/`isResizable`. `dashboard-grid.tsx` uses the new API.
- `metrics-chart.tsx` always calls three `useMetricsQuery` hooks to respect Rules of Hooks (one per series — histograms use all three, counter/gauge only the first). The extras receive `null` DSL and are disabled, so no wasted HTTP.
- Live tail uses native `EventSource`. SSE "`: ready`" / "`: keepalive`" comments are ignored (no `data:` prefix), and only `data:`-prefixed JSON frames append to the rolling 500-item buffer.
- Paginated log explorer resets via the idiomatic "derived state from props" pattern (state + key comparison during render), not useEffect + setState.

## Readiness for 13-06c (Robot E2E)

Ready. All interactive elements carry `data-testid` attributes:

- `heading-monitoring*`, `monitoring-nav-*`
- `monitoring-timerange-{15m|1h|24h|7d|custom|from|to}`
- `monitoring-log-{body-search,sev-*,row-*,load-more,explorer,live-tail}`
- `monitoring-livetail-{pause,resume,clear,row-*}`
- `monitoring-metric-{search,kind-*,<key>}`, `monitoring-metrics-{bucket,add-to-dash}`
- `monitoring-traces-{service,name,error-only,row-*}`, `monitoring-trace-span-*`
- `monitoring-dashboard-{new,name,card-*,delete-*,add-panel}`, `monitoring-panel-title`, `monitoring-panel-*`
- `monitoring-filter-{add,field-N,op-N,value-N,remove-N}`

Suggested E2E suite structure:
```
tests/e2e/monitoring/
  01_overview.robot
  02_logs.robot
  03_metrics.robot
  04_traces.robot
  05_dashboards.robot
```
