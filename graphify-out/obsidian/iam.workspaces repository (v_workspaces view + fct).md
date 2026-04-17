---
source_file: "backend/02_features/03_iam/sub_features/02_workspaces/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.workspaces repository (v_workspaces view + fct)

## Connections
- [[DB table 03_iam.11_fct_workspaces]] - `references` [EXTRACTED]
- [[DB table 03_iam.20_dtl_attr_defs (attribute definitions)]] - `references` [EXTRACTED]
- [[DB table 03_iam.21_dtl_attrs (EAV attribute store)]] - `references` [EXTRACTED]
- [[DB view 03_iam.v_workspaces]] - `references` [EXTRACTED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature