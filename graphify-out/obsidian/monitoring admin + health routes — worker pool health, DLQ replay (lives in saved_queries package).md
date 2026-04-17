---
source_file: "backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring admin + health routes — worker pool health, DLQ replay (lives in saved_queries package)

## Connections
- [[NATS DLQ subject monitoring.dlq.logs]] - `references` [EXTRACTED]
- [[NATS DLQ subject monitoring.dlq.spans]] - `references` [EXTRACTED]
- [[NATS JetStream — async message transport for OTLP ingest pipeline]] - `calls` [EXTRACTED]
- [[monitoring.saved_queries routes — CRUD + run endpoint]] - `conceptually_related_to` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation