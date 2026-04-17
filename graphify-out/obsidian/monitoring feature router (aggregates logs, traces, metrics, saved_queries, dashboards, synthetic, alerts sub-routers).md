---
source_file: "backend/02_features/05_monitoring/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring feature router (aggregates logs, traces, metrics, saved_queries, dashboards, synthetic, alerts sub-routers)

## Connections
- [[monitoring JetStream bootstrap (MONITORING_LOGS 72h2GB, MONITORING_SPANS 24h4GB, MONITORING_DLQ 7d1GB — idempotent createupdate)]] - `conceptually_related_to` [INFERRED]
- [[monitoring.metrics FastAPI routes (POST register, GET list, GET one, POST incrementsetobserve, POST query)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation