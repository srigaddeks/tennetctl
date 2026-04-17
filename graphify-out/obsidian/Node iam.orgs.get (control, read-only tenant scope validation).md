---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_get.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# Node: iam.orgs.get (control, read-only tenant scope validation)

## Connections
- [[Concept Org - Workspace - Application tenancy hierarchy]] - `rationale_for` [INFERRED]
- [[Node iam.workspaces.create (effect, validate org + create workspace)]] - `calls` [INFERRED]
- [[featureflags.flags service]] - `calls` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `calls` [EXTRACTED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature