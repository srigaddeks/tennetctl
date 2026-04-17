---
type: community
cohesion: 0.07
members: 47
---

# Monitoring Dashboards Backend

**Cohesion:** 0.07 - loosely connected
**Members:** 47 nodes

## Members
- [[.run()_47]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[.run()_48]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[.run()_51]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[.run()_50]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[DeleteDashboard]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[ForbiddenError]] - code - backend/01_core/errors.py
- [[GetDashboard]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[Input_44]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[Input_45]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[Input_48]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[Input_47]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[ListDashboards]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[Output_44]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[Output_45]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[Output_48]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[Output_47]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[UpdateDashboard]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[_utcnow()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[create_panel()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[delete_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[delete_dashboard.py]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[delete_panel()_1]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[delete_panel()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[get_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[get_dashboard.py]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[get_dashboard_by_id()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[get_panel()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[get_panel_by_id()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[insert_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[insert_panel()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[list_dashboards()_1]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[list_dashboards()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[list_dashboards.py]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[list_panels()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[list_panels_for_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[monitoring.dashboards.delete — soft-delete a dashboard.]] - rationale - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[monitoring.dashboards.get — read a dashboard.]] - rationale - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[monitoring.dashboards.list — list dashboards visible to the caller.]] - rationale - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[monitoring.dashboards.update — update a dashboard.]] - rationale - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[repository.py_29]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[service.py_30]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[soft_delete_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[update_dashboard()_1]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[update_dashboard()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[update_dashboard.py]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[update_panel()_1]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[update_panel()]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Dashboards_Backend
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_Service & Repository Layer]]
- 10 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 8 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 4 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 4 edges to [[_COMMUNITY_Auth & Error Handling]]
- 1 edge to [[_COMMUNITY_Admin Routes & DLQ]]

## Top bridge nodes
- [[ForbiddenError]] - degree 13, connects to 3 communities
- [[create_panel()]] - degree 7, connects to 2 communities
- [[delete_dashboard()]] - degree 7, connects to 2 communities
- [[repository.py_29]] - degree 12, connects to 1 community
- [[service.py_30]] - degree 12, connects to 1 community