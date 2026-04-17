---
type: community
cohesion: 0.09
members: 24
---

# Audit Frontend

**Cohesion:** 0.09 - loosely connected
**Members:** 24 nodes

## Members
- [[AuditBucket type (hour  day)]] - code - frontend/src/features/audit-analytics/_components/filter-bar.tsx
- [[AuditEventFilter (type)]] - code - frontend/src/types/api.ts
- [[AuditEventFilter type (event_key, category_code, outcome, actor_user_id, q)]] - code - frontend/src/features/audit-analytics/_components/filter-bar.tsx
- [[AuditEventRow type (event_key, category_code, outcome, actor_user_id, org_id)]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[AuditFunnelRequest  AuditFunnelResponse  AuditFunnelStep (types)]] - code - frontend/src/types/api.ts
- [[AuditRetentionBucket (type)]] - code - frontend/src/types/api.ts
- [[EventDetailDrawer component (audit)_1]] - code - frontend/src/features/audit-analytics/_components/event-detail-drawer.tsx
- [[EventsTable component (audit)_1]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[FilterBar component (audit)_1]] - code - frontend/src/features/audit-analytics/_components/filter-bar.tsx
- [[Funnel analysis (ordered event steps, conversion pct, bar chart)]] - document - frontend/src/features/audit-analytics/_components/funnel-builder.tsx
- [[FunnelBuilder]] - code - frontend/src/features/audit-analytics/_components/funnel-builder.tsx
- [[GET v1audit-events]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[GET v1audit-eventsretention]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[POST v1audit-eventsfunnel]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[Retention analysis (anchor event + return event + bucket + cohort grid)]] - document - frontend/src/features/audit-analytics/_components/retention-grid.tsx
- [[RetentionGrid]] - code - frontend/src/features/audit-analytics/_components/retention-grid.tsx
- [[SavedViewsPanel component (audit)]] - code - frontend/src/features/audit-analytics/_components/saved-views-panel.tsx
- [[StatsPanel]] - code - frontend/src/features/audit-analytics/_components/stats-panel.tsx
- [[use-audit-events hooks (useAuditEventDetail, useAuditSavedViews, useCreateSavedView, useDeleteSavedView)]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEventStats]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEvents]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditFunnel]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditRetention]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditSavedViews  useCreateSavedView  useDeleteSavedView]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Frontend
SORT file.name ASC
```
