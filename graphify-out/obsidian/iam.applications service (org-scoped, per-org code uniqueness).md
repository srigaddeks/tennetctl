---
source_file: "backend/02_features/03_iam/sub_features/06_applications/service.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.applications service (org-scoped, per-org code uniqueness)

## Connections
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - `implements` [INFERRED]
- [[Node audit.events.emit (audit event sink)]] - `calls` [EXTRACTED]
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `calls` [EXTRACTED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[iam.applications repository (v_applications + lnk_application_scopes)]] - `calls` [EXTRACTED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature