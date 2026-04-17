---
source_file: "backend/02_features/03_iam/sub_features/07_memberships/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.memberships service layer

## Connections
- [[Concept Org membership (user-org lnk, immutable, hard-delete on revoke)]] - `implements` [EXTRACTED]
- [[Concept Workspace membership (user-workspace lnk, org_id auto-derived, immutable)]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[Node audit.events.emit]] - `calls` [EXTRACTED]
- [[Node iam.memberships.org.assign (effect)]] - `calls` [EXTRACTED]
- [[Node iam.memberships.org.revoke (effect)]] - `calls` [EXTRACTED]
- [[Node iam.memberships.workspace.assign (effect)]] - `calls` [EXTRACTED]
- [[Node iam.memberships.workspace.revoke (effect)]] - `calls` [EXTRACTED]
- [[Node iam.users.get (control)]] - `conceptually_related_to` [EXTRACTED]
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.memberships FastAPI routes]] - `calls` [EXTRACTED]
- [[iam.memberships asyncpg repository]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization