---
source_file: "backend/02_features/03_iam/sub_features/06_applications/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.applications repository (v_applications + lnk_application_scopes)

## Connections
- [[DB table 03_iam.03_dim_scopes]] - `references` [EXTRACTED]
- [[DB table 03_iam.15_fct_applications]] - `references` [EXTRACTED]
- [[DB table 03_iam.21_dtl_attrs (EAV attribute store)]] - `references` [EXTRACTED]
- [[DB table 03_iam.45_lnk_application_scopes (many-to-many)]] - `references` [EXTRACTED]
- [[DB view 03_iam.v_applications]] - `references` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature