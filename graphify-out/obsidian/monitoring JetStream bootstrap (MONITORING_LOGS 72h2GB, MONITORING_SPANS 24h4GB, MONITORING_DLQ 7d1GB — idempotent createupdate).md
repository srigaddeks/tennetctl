---
source_file: "backend/02_features/05_monitoring/bootstrap/jetstream.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring JetStream bootstrap (MONITORING_LOGS 72h/2GB, MONITORING_SPANS 24h/4GB, MONITORING_DLQ 7d/1GB — idempotent create/update)

## Connections
- [[NATS JetStream streams for monitoring workqueue retention for logsspans, limits retention for DLQ]] - `implements` [EXTRACTED]
- [[monitoring feature router (aggregates logs, traces, metrics, saved_queries, dashboards, synthetic, alerts sub-routers)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation