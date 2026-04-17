---
source_file: "backend/02_features/05_monitoring/sub_features/03_traces/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.traces service — query DSL + OTLP traces publish pipeline

## Connections
- [[NATS JetStream — async message transport for OTLP ingest pipeline]] - `calls` [EXTRACTED]
- [[Node monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)]] - `calls` [INFERRED]
- [[monitoring.query_dsl — shared DSL validation and compilation for logs, metrics, traces]] - `calls` [EXTRACTED]
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - `shares_data_with` [EXTRACTED]
- [[monitoring.traces OTLP decoder — decodes ExportTraceServiceRequest, routes per ResourceSpans to JetStream subject]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation