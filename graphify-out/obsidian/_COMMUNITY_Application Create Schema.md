---
type: community
cohesion: 1.00
members: 1
---

# Application Create Schema

**Cohesion:** 1.00 - tightly connected
**Members:** 1 nodes

## Members
- [[ApplicationCreate schema (org_id, code, label, description)]] - code - backend/02_features/03_iam/sub_features/06_applications/schemas.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Application_Create_Schema
SORT file.name ASC
```
