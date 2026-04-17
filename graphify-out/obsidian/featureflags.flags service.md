---
source_file: "backend/02_features/09_featureflags/sub_features/01_flags/service.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# featureflags.flags service

## Connections
- [[Node audit.events.emit (audit event sink)]] - `calls` [EXTRACTED]
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - `calls` [EXTRACTED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[featureflags.flags repository]] - `calls` [EXTRACTED]
- [[featureflags.flags routes]] - `calls` [EXTRACTED]
- [[node iam.applications.get]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature