---
type: community
cohesion: 0.20
members: 10
---

# Monitoring Panel & Query Hooks

**Cohesion:** 0.20 - loosely connected
**Members:** 10 nodes

## Members
- [[LogStreamPanel()]] - code - frontend/src/features/monitoring/_components/panel.tsx
- [[Panel()]] - code - frontend/src/features/monitoring/_components/panel.tsx
- [[TraceListPanel()]] - code - frontend/src/features/monitoring/_components/panel.tsx
- [[panel.tsx]] - code - frontend/src/features/monitoring/_components/panel.tsx
- [[use-logs-query.ts]] - code - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[use-traces-query.ts]] - code - frontend/src/features/monitoring/hooks/use-traces-query.ts
- [[useLogsQuery()]] - code - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[useLogsQueryMore()]] - code - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[useTraceDetail()]] - code - frontend/src/features/monitoring/hooks/use-traces-query.ts
- [[useTracesQuery()]] - code - frontend/src/features/monitoring/hooks/use-traces-query.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Panel_&_Query_Hooks
SORT file.name ASC
```
