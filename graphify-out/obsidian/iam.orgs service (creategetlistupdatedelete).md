---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/service.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.orgs service (create/get/list/update/delete)

## Connections
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - `implements` [INFERRED]
- [[Node audit.events.emit (audit event sink)]] - `calls` [EXTRACTED]
- [[Node iam.orgs.create (effect, fct+dtl+audit atomic write)]] - `calls` [EXTRACTED]
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `calls` [EXTRACTED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `conceptually_related_to` [INFERRED]
- [[iam.orgs repository (v_orgs view + fct)]] - `calls` [EXTRACTED]
- [[iam.orgs routes (v1orgs)]] - `calls` [EXTRACTED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature