---
type: community
cohesion: 1.00
members: 2
---

# Audit Tail Endpoint & Hook

**Cohesion:** 1.00 - tightly connected
**Members:** 2 nodes

## Members
- [[GET v1audit-eventstail]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuditTailPoll  useOutboxCursor]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Tail_Endpoint_&_Hook
SORT file.name ASC
```
