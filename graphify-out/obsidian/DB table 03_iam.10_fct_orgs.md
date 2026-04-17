---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# DB table: 03_iam.10_fct_orgs

## Connections
- [[Concept Org - Workspace - Application tenancy hierarchy]] - `conceptually_related_to` [INFERRED]
- [[DB table 03_iam.11_fct_workspaces]] - `references` [EXTRACTED]
- [[DB table 03_iam.15_fct_applications]] - `references` [EXTRACTED]
- [[DB table 03_iam.28_fct_iam_api_keys]] - `references` [EXTRACTED]
- [[iam.orgs repository (v_orgs view + fct)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature