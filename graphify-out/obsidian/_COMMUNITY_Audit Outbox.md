---
type: community
cohesion: 0.15
members: 15
---

# Audit Outbox

**Cohesion:** 0.15 - loosely connected
**Members:** 15 nodes

## Members
- [[.run()_63]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[AuditEventsSubscribe]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[Input_60]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[Output_60]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[Return events from the outbox newer than `since_id`.     Joins with v_audit_even]] - rationale - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[Return the current max outbox id (0 if empty). Used to initialise cursors.]] - rationale - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[audit.events.subscribe — control node.  Polling-based outbox consumer. Callers (]] - rationale - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[current_cursor()]] - code - backend/02_features/04_audit/sub_features/03_outbox/service.py
- [[latest_outbox_id()]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[poll()]] - code - backend/02_features/04_audit/sub_features/03_outbox/service.py
- [[poll_outbox()]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[repository.py_37]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[reset_dim_cache()]] - code - backend/01_catalog/repository.py
- [[service.py_39]] - code - backend/02_features/04_audit/sub_features/03_outbox/service.py
- [[subscribe_events.py]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Outbox
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Service & Repository Layer]]
- 4 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 1 edge to [[_COMMUNITY_Audit Emit Pipeline]]
- 1 edge to [[_COMMUNITY_Alert Evaluator Worker]]

## Top bridge nodes
- [[reset_dim_cache()]] - degree 3, connects to 2 communities
- [[poll_outbox()]] - degree 5, connects to 1 community
- [[latest_outbox_id()]] - degree 4, connects to 1 community
- [[.run()_63]] - degree 4, connects to 1 community
- [[repository.py_37]] - degree 3, connects to 1 community