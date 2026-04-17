---
source_file: "backend/02_features/03_iam/sub_features/07_memberships/service.py"
type: "document"
community: "Error Types & Authorization"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/Error_Types_&_Authorization
---

# Concept: Org membership (user-org lnk, immutable, hard-delete on revoke)

## Connections
- [[Concept Single-tenant default org auto-attach on signupsignin]] - `conceptually_related_to` [EXTRACTED]
- [[DB table 03_iam.40_lnk_user_orgs (org memberships)]] - `implements` [INFERRED]
- [[Node iam.memberships.org.assign (effect)]] - `implements` [INFERRED]
- [[Node iam.memberships.org.revoke (effect)]] - `implements` [INFERRED]
- [[iam.memberships service layer]] - `implements` [EXTRACTED]

#graphify/document #graphify/INFERRED #community/Error_Types_&_Authorization