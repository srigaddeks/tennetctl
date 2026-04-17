---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# DB table: 03_iam.21_dtl_attrs (EAV attribute store)

## Connections
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - `conceptually_related_to` [EXTRACTED]
- [[iam.applications repository (v_applications + lnk_application_scopes)]] - `references` [EXTRACTED]
- [[iam.orgs repository (v_orgs view + fct)]] - `references` [EXTRACTED]
- [[iam.workspaces repository (v_workspaces view + fct)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature