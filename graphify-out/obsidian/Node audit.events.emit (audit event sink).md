---
source_file: "backend/02_features/04_audit/"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# Node: audit.events.emit (audit event sink)

## Connections
- [[SyntheticRunner_1]] - `calls` [EXTRACTED]
- [[featureflags.flags service]] - `calls` [EXTRACTED]
- [[iam.api_keys service (mintrevokevalidate machine tokens)]] - `calls` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `calls` [EXTRACTED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature