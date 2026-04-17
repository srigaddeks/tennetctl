---
source_file: "backend/02_features/05_monitoring/sub_features/07_alerts/service.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L379"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Return the latest firing event row for (rule_id, fingerprint) or None.

## Connections
- [[find_firing_event()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker