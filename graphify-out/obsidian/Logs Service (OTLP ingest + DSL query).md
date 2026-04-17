---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Logs Service (OTLP ingest + DSL query)

## Connections
- [[Monitoring Query DSL (validate + compile metricslogs)]] - `calls` [EXTRACTED]
- [[NATS JetStream (log publish target)]] - `calls` [EXTRACTED]
- [[Node monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[Node monitoring.logs.query — DSL query node (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[Node monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)]] - `calls` [INFERRED]
- [[OTLP Logs Decoder (protobufJSON → JetStream batches)]] - `calls` [EXTRACTED]
- [[monitoring.logs routes — OTLP ingest + query + SSE live-tail]] - `calls` [EXTRACTED]
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - `shares_data_with` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation