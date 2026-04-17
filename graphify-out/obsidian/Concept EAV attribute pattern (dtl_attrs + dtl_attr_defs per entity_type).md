---
source_file: "backend/02_features/03_iam/"
type: "document"
community: "API Keys Sub-feature"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# Concept: EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)

## Connections
- [[ADR-006 Database Schema Structure and Naming Conventions]] - `implements` [EXTRACTED]
- [[ADR-028 vault envelope encryption rationale]] - `references` [EXTRACTED]
- [[DB table 03_iam.20_dtl_attr_defs (attribute definitions)]] - `conceptually_related_to` [EXTRACTED]
- [[DB table 03_iam.21_dtl_attrs (EAV attribute store)]] - `conceptually_related_to` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `implements` [INFERRED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `implements` [INFERRED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `implements` [INFERRED]

#graphify/document #graphify/EXTRACTED #community/API_Keys_Sub-feature