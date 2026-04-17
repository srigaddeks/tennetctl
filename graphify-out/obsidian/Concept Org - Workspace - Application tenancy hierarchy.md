---
source_file: "backend/02_features/03_iam/"
type: "document"
community: "API Keys Sub-feature"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/API_Keys_Sub-feature
---

# Concept: Org -> Workspace -> Application tenancy hierarchy

## Connections
- [[DB table 03_iam.10_fct_orgs]] - `conceptually_related_to` [INFERRED]
- [[DB table 03_iam.11_fct_workspaces]] - `conceptually_related_to` [INFERRED]
- [[DB table 03_iam.15_fct_applications]] - `conceptually_related_to` [INFERRED]
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `rationale_for` [INFERRED]
- [[WorkspaceCreate schema (org_id, slug, display_name)]] - `conceptually_related_to` [INFERRED]

#graphify/document #graphify/INFERRED #community/API_Keys_Sub-feature