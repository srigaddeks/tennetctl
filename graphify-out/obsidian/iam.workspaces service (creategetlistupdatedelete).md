---
source_file: "backend/02_features/03_iam/sub_features/02_workspaces/service.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.workspaces service (create/get/list/update/delete)

## Connections
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - `implements` [INFERRED]
- [[Node audit.events.emit (audit event sink)]] - `calls` [EXTRACTED]
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `calls` [EXTRACTED]
- [[Node iam.workspaces.create (effect, validate org + create workspace)]] - `calls` [EXTRACTED]
- [[Node iam.workspaces.get (control, read-only cross-sub-feature lookup)]] - `calls` [EXTRACTED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `conceptually_related_to` [INFERRED]
- [[iam.workspaces repository (v_workspaces view + fct)]] - `calls` [EXTRACTED]
- [[iam.workspaces routes (v1workspaces)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature