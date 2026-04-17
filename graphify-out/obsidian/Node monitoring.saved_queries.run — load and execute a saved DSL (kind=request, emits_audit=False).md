---
source_file: "backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Node: monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)

## Connections
- [[Catalog Node Base Class]] - `implements` [EXTRACTED]
- [[Logs Service (OTLP ingest + DSL query)]] - `calls` [INFERRED]
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - `calls` [EXTRACTED]
- [[monitoring.traces service — query DSL + OTLP traces publish pipeline]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation