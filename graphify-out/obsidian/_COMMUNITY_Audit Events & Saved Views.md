---
type: community
cohesion: 0.04
members: 72
---

# Audit Events & Saved Views

**Cohesion:** 0.04 - loosely connected
**Members:** 72 nodes

## Members
- [[AuditSavedViewRow]] - code - backend/02_features/04_audit/sub_features/02_saved_views/schemas.py
- [[Build WHERE fragment + positional params list from a filter dict.     Only non-N]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Cohort retention actors who did `anchor` are grouped by cohort_period     (date]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Cohort retention group actors by the weekday they first did `anchor`,     then]] - rationale - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[Compute aggregates top-50 by event_key, all outcomes, all categories,     time-]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Count actors who did current_key AFTER prev_key (any occurrence before).]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Cross-org guard. If the caller's session has an org_id bound, the filter     org]] - rationale - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[Decode cursor → (created_at, id). Raises ValueError on malformed input.]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Delete by id + org_id guard. Returns True if a row was deleted.]] - rationale - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[Emit audit.events.queried so the audit log records who inspected it.]] - rationale - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[Encode (created_at, id) into an opaque base64url string.]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Idempotent upsert for auto-sync of observed event keys. Resolves category_code]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[Return (items, next_cursor). items has up to `limit` rows ordered by     created]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[SavedViewsPanel()]] - code - frontend/src/features/audit-analytics/_components/saved-views-panel.tsx
- [[Simplified funnel each step is a separate fetchval call with explicit params.]] - rationale - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_build_where()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_decode_cursor()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_emit_queried()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[_encode_cursor()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_enforce_org_authz()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[_funnel_step0()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_funnel_stepi()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[_require_org()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[_session_scope()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[create_saved_view()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[create_saved_view_route()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[create_view()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/service.py
- [[delete_saved_view()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[delete_saved_view_route()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[delete_view()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/service.py
- [[filterParams()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[funnel()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[funnel_analysis()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[get_event()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[get_saved_view()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[list_audit_event_keys_route()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[list_audit_events_route()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[list_event_keys()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[list_events()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[list_keys()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[list_saved_views()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[list_saved_views_route()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[list_views()]] - code - backend/02_features/04_audit/sub_features/02_saved_views/service.py
- [[repository.py_35]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[repository.py_36]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[retention()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[retention_analysis()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[retention_route()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[routes.py_44]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[routes.py_45]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[saved-views-panel.tsx]] - code - frontend/src/features/audit-analytics/_components/saved-views-panel.tsx
- [[service.py_37]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[service.py_38]] - code - backend/02_features/04_audit/sub_features/02_saved_views/service.py
- [[stats()_1]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[stats()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[stats_audit_events_route()]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[upsert_event_key()]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[upsert_key()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[use-audit-events.ts]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEventDetail()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEventKeys()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEventStats()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditEvents()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditFunnel()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditRetention()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditSavedViews()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditTailPoll()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useCreateSavedView()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useDeleteSavedView()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useInvalidateAuditEvents()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useLoadMore()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useOutboxCursor()]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Events_&_Saved_Views
SORT file.name ASC
```

## Connections to other communities
- 15 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 12 edges to [[_COMMUNITY_Service & Repository Layer]]
- 11 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 2 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 1 edge to [[_COMMUNITY_Core Infrastructure]]
- 1 edge to [[_COMMUNITY_Auth & Error Handling]]

## Top bridge nodes
- [[list_audit_events_route()]] - degree 7, connects to 4 communities
- [[_session_scope()]] - degree 12, connects to 3 communities
- [[routes.py_44]] - degree 13, connects to 2 communities
- [[service.py_37]] - degree 8, connects to 2 communities
- [[list_events()]] - degree 7, connects to 2 communities