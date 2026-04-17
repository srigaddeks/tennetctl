---
source_file: "backend/02_features/05_monitoring/workers/alert_evaluator_worker.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# AlertEvaluatorWorker

## Connections
- [[CounterHandle_1]] - `calls` [EXTRACTED]
- [[DB view v_monitoring_alert_rules]] - `calls` [EXTRACTED]
- [[GaugeHandle_1]] - `calls` [EXTRACTED]
- [[WorkerPool supervisor]] - `calls` [EXTRACTED]
- [[node notify.send.transactional]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature