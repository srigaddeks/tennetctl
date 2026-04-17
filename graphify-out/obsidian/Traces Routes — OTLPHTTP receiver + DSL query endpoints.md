---
source_file: "backend/02_features/05_monitoring/sub_features/03_traces/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Alert_Rules_&_Evaluation
---

# Traces Routes — OTLP/HTTP receiver + DSL query endpoints

## Connections
- [[NATS JetStream (log publish target)]] - `calls` [EXTRACTED]
- [[OtlpTracesIngest — node key monitoring.traces.otlp_ingest (request kind)]] - `conceptually_related_to` [INFERRED]
- [[Traces Repository (empty — writes delegated to 13-04 consumer)]] - `references` [INFERRED]
- [[TracesQueryNode — node key monitoring.traces.query (request kind)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/INFERRED #community/Alert_Rules_&_Evaluation