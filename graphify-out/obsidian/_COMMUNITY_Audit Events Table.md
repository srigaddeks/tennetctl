---
type: community
cohesion: 0.40
members: 5
---

# Audit Events Table

**Cohesion:** 0.40 - moderately connected
**Members:** 5 nodes

## Members
- [[abbreviate()]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[categoryTone()]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[events-table.tsx]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[outcomeTone()]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[relTime()]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Events_Table
SORT file.name ASC
```
