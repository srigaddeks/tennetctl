---
source_file: "backend/01_catalog/__init__.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# backend.01_catalog.run_node (cross-sub-feature node dispatch)

## Connections
- [[CounterHandle_1]] - `calls` [EXTRACTED]
- [[GaugeHandle_1]] - `calls` [EXTRACTED]
- [[HistogramHandle_1]] - `calls` [EXTRACTED]
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - `calls` [EXTRACTED]
- [[featureflags.flags service]] - `calls` [EXTRACTED]
- [[iam.api_keys service (mintrevokevalidate machine tokens)]] - `calls` [EXTRACTED]
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - `calls` [EXTRACTED]
- [[iam.orgs service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]
- [[iam.workspaces service (creategetlistupdatedelete)]] - `calls` [EXTRACTED]
- [[vault.configs service (createlistgetupdatedelete config)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature