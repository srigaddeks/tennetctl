---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.logs routes — OTLP ingest + query + SSE live-tail

## Connections
- [[DB view 05_monitoring.v_monitoring_logs — read view for log tail and queries]] - `references` [EXTRACTED]
- [[Logs Service (OTLP ingest + DSL query)]] - `calls` [EXTRACTED]
- [[NATS JetStream — async message transport for OTLP ingest pipeline]] - `calls` [EXTRACTED]
- [[NATS subject pattern monitoring.logs.otel.{service} — OTLP logs per service]] - `references` [EXTRACTED]
- [[Node monitoring.logs.query — DSL query node (kind=request, emits_audit=False)]] - `semantically_similar_to` [INFERRED]
- [[NotifyListener worker — Postgres LISTENNOTIFY broadcaster for log tail SSE]] - `references` [EXTRACTED]
- [[monitoring.query_dsl — shared DSL validation and compilation for logs, metrics, traces]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation