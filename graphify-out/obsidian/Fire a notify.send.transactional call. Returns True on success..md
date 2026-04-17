---
source_file: "backend/02_features/05_monitoring/workers/alert_evaluator_worker.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L127"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Fire a notify.send.transactional call. Returns True on success.

## Connections
- [[._notify()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker