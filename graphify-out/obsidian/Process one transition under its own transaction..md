---
source_file: "backend/02_features/05_monitoring/workers/alert_evaluator_worker.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L180"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Process one transition under its own transaction.

## Connections
- [[._handle_transition()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker