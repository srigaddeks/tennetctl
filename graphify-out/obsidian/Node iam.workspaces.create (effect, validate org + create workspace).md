---
source_file: "backend/02_features/03_iam/sub_features/02_workspaces/nodes/iam_workspaces_create.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# Node: iam.workspaces.create (effect, validate org + create workspace)

## Connections
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `calls` [INFERRED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature