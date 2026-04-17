---
type: community
cohesion: 0.67
members: 3
---

# IAM Applications Nodes

**Cohesion:** 0.67 - moderately connected
**Members:** 3 nodes

## Members
- [[Node iam.applications.create (effect)]] - code - backend/02_features/03_iam/sub_features/06_applications/nodes/iam_applications_create.py
- [[Node iam.applications.get (control)]] - code - backend/02_features/03_iam/sub_features/06_applications/nodes/iam_applications_get.py
- [[iam.applications routes (FastAPI)]] - code - backend/02_features/03_iam/sub_features/06_applications/routes.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/IAM_Applications_Nodes
SORT file.name ASC
```
