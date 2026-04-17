---
source_file: "backend/02_features/03_iam/sub_features/06_applications/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# DB table: 03_iam.03_dim_scopes

## Connections
- [[DB table 03_iam.45_lnk_application_scopes (many-to-many)]] - `references` [EXTRACTED]
- [[iam.applications repository (v_applications + lnk_application_scopes)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature