---
source_file: "backend/02_features/03_iam/sub_features/07_memberships/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.memberships asyncpg repository

## Connections
- [[DB table 03_iam.40_lnk_user_orgs (org memberships)]] - `references` [EXTRACTED]
- [[DB table 03_iam.41_lnk_user_workspaces (workspace memberships)]] - `references` [EXTRACTED]
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.memberships service layer]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization