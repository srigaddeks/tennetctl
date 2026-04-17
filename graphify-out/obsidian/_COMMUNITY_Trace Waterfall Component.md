---
type: community
cohesion: 1.00
members: 2
---

# Trace Waterfall Component

**Cohesion:** 1.00 - tightly connected
**Members:** 2 nodes

## Members
- [[Trace Waterfall (span tree flattened by parent_span_id, depth-indented, jk keyboard nav)]] - document - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[TraceWaterfall Component]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Trace_Waterfall_Component
SORT file.name ASC
```
