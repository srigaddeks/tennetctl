---
type: community
cohesion: 0.07
members: 39
---

# Alerts UI & IAM Users

**Cohesion:** 0.07 - loosely connected
**Members:** 39 nodes

## Members
- [[API Endpoint v1monitoringalert-rules (CRUD + pauseunpause)]] - document - frontend/src/features/monitoring/hooks/use-alerts.ts
- [[API Endpoint v1monitoringalerts (events + silence-from-event)]] - document - frontend/src/features/monitoring/hooks/use-alerts.ts
- [[API Endpoint v1monitoringsilences (CRUD)]] - document - frontend/src/features/monitoring/hooks/use-alerts.ts
- [[API Endpoint v1users (IAM Users CRUD)]] - document - frontend/src/features/iam-users/hooks/use-users.ts
- [[API Endpoint GET v1monitoringlogstail (SSE)]] - document - frontend/src/features/monitoring/hooks/use-live-tail.ts
- [[API Endpoint GET v1monitoringmetrics (metric definitions list)]] - document - frontend/src/features/monitoring/hooks/use-metrics-list.ts
- [[API Endpoint POST v1monitoringlogsquery]] - document - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[API Endpoint POST v1monitoringmetricsquery]] - document - frontend/src/features/monitoring/hooks/use-metrics-query.ts
- [[API Endpoint POST v1monitoringtracesquery]] - document - frontend/src/features/monitoring/hooks/use-traces-query.ts
- [[Alert Severity Levels (infowarnerrorcritical)]] - document - frontend/src/features/monitoring/_components/alert-list.tsx
- [[Alert State (firingresolved) + Silenced overlay]] - document - frontend/src/features/monitoring/_components/alert-list.tsx
- [[AlertList Component]] - code - frontend/src/features/monitoring/_components/alert-list.tsx
- [[AlertRuleEditor Component]] - code - frontend/src/features/monitoring/_components/alert-rule-editor.tsx
- [[DSL Filter Model (eqnecontainsin + and combinator)]] - document - frontend/src/features/monitoring/_components/dsl-filter-builder.tsx
- [[DashboardGrid Component]] - code - frontend/src/features/monitoring/_components/dashboard-grid.tsx
- [[DslFilterBuilder Component]] - code - frontend/src/features/monitoring/_components/dsl-filter-builder.tsx
- [[LogExplorer Component]] - code - frontend/src/features/monitoring/_components/log-explorer.tsx
- [[LogLiveTail Component]] - code - frontend/src/features/monitoring/_components/log-live-tail.tsx
- [[Metric Kind (countergaugehistogram)]] - document - frontend/src/features/monitoring/_components/metric-picker.tsx
- [[MetricPicker Component]] - code - frontend/src/features/monitoring/_components/metric-picker.tsx
- [[MetricsChart Component]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[Monitoring Query DSL (target metricslogstraces + timerange + aggregate + bucket)]] - document - frontend/src/features/monitoring/_components/alert-rule-editor.tsx
- [[Panel Component (Dashboard Panel)]] - code - frontend/src/features/monitoring/_components/panel.tsx
- [[Panel Types (timeseriesstattablelog_streamtrace_list)]] - document - frontend/src/features/monitoring/_components/panel.tsx
- [[Recharts Library (LineChart, ResponsiveContainer)]] - document - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[SSE Live Tail (EventSource, 500-event rolling buffer, pauseresumeclear)]] - document - frontend/src/features/monitoring/hooks/use-live-tail.ts
- [[SilenceDialog Component]] - code - frontend/src/features/monitoring/_components/silence-dialog.tsx
- [[Timerange Model (last token presets 15m1h24h7d or custom from_tsto_ts)]] - document - frontend/src/features/monitoring/_components/timerange-picker.tsx
- [[TimerangePicker Component]] - code - frontend/src/features/monitoring/_components/timerange-picker.tsx
- [[react-grid-layout Library (ResponsiveGridLayout, drag+resize)]] - document - frontend/src/features/monitoring/_components/dashboard-grid.tsx
- [[useAlertRules Hook (re-export facade)]] - code - frontend/src/features/monitoring/hooks/use-alert-rules.ts
- [[useAlerts Hook (alert rules + events + silences)]] - code - frontend/src/features/monitoring/hooks/use-alerts.ts
- [[useLiveTail Hook (SSE log stream)]] - code - frontend/src/features/monitoring/hooks/use-live-tail.ts
- [[useLogsQuery Hook (cursor pagination)]] - code - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[useMetricsList Hook]] - code - frontend/src/features/monitoring/hooks/use-metrics-list.ts
- [[useMetricsQuery Hook]] - code - frontend/src/features/monitoring/hooks/use-metrics-query.ts
- [[useSilences Hook (re-export facade)]] - code - frontend/src/features/monitoring/hooks/use-silences.ts
- [[useTracesQuery + useTraceDetail Hooks]] - code - frontend/src/features/monitoring/hooks/use-traces-query.ts
- [[useUsers Hook (IAM Users CRUD)]] - code - frontend/src/features/iam-users/hooks/use-users.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Alerts_UI_&_IAM_Users
SORT file.name ASC
```
