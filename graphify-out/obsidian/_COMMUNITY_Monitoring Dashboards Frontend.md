---
type: community
cohesion: 0.22
members: 9
---

# Monitoring Dashboards Frontend

**Cohesion:** 0.22 - loosely connected
**Members:** 9 nodes

## Members
- [[use-dashboards.ts]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useCreateDashboard()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useCreatePanel()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useDashboard()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useDashboards()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useDeleteDashboard()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useDeletePanel()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useUpdateDashboard()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useUpdatePanel()]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Dashboards_Frontend
SORT file.name ASC
```
