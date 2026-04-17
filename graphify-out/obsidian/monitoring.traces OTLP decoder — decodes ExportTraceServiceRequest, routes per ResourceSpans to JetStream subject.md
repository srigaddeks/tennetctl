---
source_file: "backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.traces OTLP decoder — decodes ExportTraceServiceRequest, routes per ResourceSpans to JetStream subject

## Connections
- [[NATS subject pattern monitoring.traces.otel.{service} — OTLP traces per service]] - `references` [EXTRACTED]
- [[Node monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)]] - `conceptually_related_to` [INFERRED]
- [[monitoring.traces service — query DSL + OTLP traces publish pipeline]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation