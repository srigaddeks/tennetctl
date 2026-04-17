---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/nodes/otlp_ingest.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Node: monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)

## Connections
- [[Catalog Node Base Class]] - `implements` [EXTRACTED]
- [[Logs Service (OTLP ingest + DSL query)]] - `calls` [EXTRACTED]
- [[NATS JetStream — async message transport for OTLP ingest pipeline]] - `calls` [EXTRACTED]
- [[monitoring.traces OTLP decoder — decodes ExportTraceServiceRequest, routes per ResourceSpans to JetStream subject]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation