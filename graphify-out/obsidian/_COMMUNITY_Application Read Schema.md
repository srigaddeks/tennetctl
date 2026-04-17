---
type: community
cohesion: 1.00
members: 1
---

# Application Read Schema

**Cohesion:** 1.00 - tightly connected
**Members:** 1 nodes

## Members
- [[ApplicationRead schema (includes scope_ids)]] - code - backend/02_features/03_iam/sub_features/06_applications/schemas.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Application_Read_Schema
SORT file.name ASC
```
