---
source_file: "backend/02_features/05_monitoring/workers/logs_consumer.py"
type: "rationale"
community: "Monitoring Stores & Workers"
location: "L235"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Monitoring_Stores_&_Workers
---

# On insert failure: nack (redeliver) unless max_deliver exhausted.

## Connections
- [[._handle_failure()_1]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Monitoring_Stores_&_Workers