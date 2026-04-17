---
source_file: "backend/02_features/05_monitoring/stores/postgres_metrics_store.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L58"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Return True if OK to insert; False if over limit.

## Connections
- [[._check_cardinality()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker