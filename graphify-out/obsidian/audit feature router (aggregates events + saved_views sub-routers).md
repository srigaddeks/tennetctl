---
source_file: "backend/02_features/04_audit/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# audit feature router (aggregates events + saved_views sub-routers)

## Connections
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - `calls` [EXTRACTED]
- [[audit.saved_views service (listcreatedelete saved views)]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation