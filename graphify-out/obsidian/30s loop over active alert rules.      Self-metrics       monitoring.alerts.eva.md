---
source_file: "backend/02_features/05_monitoring/workers/alert_evaluator_worker.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L53"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# 30s loop over active alert rules.      Self-metrics:       monitoring.alerts.eva

## Connections
- [[AlertEvaluatorWorker]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker