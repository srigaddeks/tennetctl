---
source_file: "backend/02_features/03_iam/sub_features/07_memberships/service.py"
type: "document"
community: "Error Types & Authorization"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/Error_Types_&_Authorization
---

# Concept: Workspace membership (user-workspace lnk, org_id auto-derived, immutable)

## Connections
- [[DB table 03_iam.41_lnk_user_workspaces (workspace memberships)]] - `implements` [INFERRED]
- [[Node iam.memberships.workspace.assign (effect)]] - `rationale_for` [INFERRED]
- [[Node iam.memberships.workspace.revoke (effect)]] - `implements` [INFERRED]
- [[iam.memberships service layer]] - `implements` [EXTRACTED]

#graphify/document #graphify/INFERRED #community/Error_Types_&_Authorization