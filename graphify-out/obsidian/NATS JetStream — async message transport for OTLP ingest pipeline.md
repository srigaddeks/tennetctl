---
source_file: "backend/01_core/nats.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# NATS JetStream — async message transport for OTLP ingest pipeline

## Connections
- [[Node monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[monitoring admin + health routes — worker pool health, DLQ replay (lives in saved_queries package)]] - `calls` [EXTRACTED]
- [[monitoring.logs routes — OTLP ingest + query + SSE live-tail]] - `calls` [EXTRACTED]
- [[monitoring.traces service — query DSL + OTLP traces publish pipeline]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation