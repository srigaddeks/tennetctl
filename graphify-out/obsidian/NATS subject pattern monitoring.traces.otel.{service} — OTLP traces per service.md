---
source_file: "backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# NATS subject pattern: monitoring.traces.otel.{service} — OTLP traces per service

## Connections
- [[NATS DLQ subject monitoring.dlq.spans]] - `conceptually_related_to` [INFERRED]
- [[monitoring.traces OTLP decoder — decodes ExportTraceServiceRequest, routes per ResourceSpans to JetStream subject]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation