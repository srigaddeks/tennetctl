---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# NATS JetStream (log publish target)

## Connections
- [[Logs Service (OTLP ingest + DSL query)]] - `calls` [EXTRACTED]
- [[OTLP Logs Decoder (protobufJSON → JetStream batches)]] - `conceptually_related_to` [INFERRED]
- [[OtlpTracesIngest — node key monitoring.traces.otlp_ingest (request kind)]] - `calls` [EXTRACTED]
- [[Traces Routes — OTLPHTTP receiver + DSL query endpoints]] - `calls` [EXTRACTED]
- [[core config (frozen dataclass, env-var contract, ADR-028)]] - `references` [EXTRACTED]
- [[core nats (JetStream client singleton, backoff retry)]] - `implements` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation