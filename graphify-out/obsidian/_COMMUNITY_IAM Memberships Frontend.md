---
type: community
cohesion: 0.29
members: 7
---

# IAM Memberships Frontend

**Cohesion:** 0.29 - loosely connected
**Members:** 7 nodes

## Members
- [[use-memberships.ts]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useCreateOrgMembership()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useCreateWorkspaceMembership()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useDeleteOrgMembership()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useDeleteWorkspaceMembership()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useOrgMemberships()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useWorkspaceMemberships()]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/IAM_Memberships_Frontend
SORT file.name ASC
```
