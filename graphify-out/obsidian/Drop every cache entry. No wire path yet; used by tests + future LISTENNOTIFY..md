---
source_file: "backend/02_features/02_vault/client.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L58"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Drop every cache entry. No wire path yet; used by tests + future LISTEN/NOTIFY.

## Connections
- [[.invalidate_all()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker