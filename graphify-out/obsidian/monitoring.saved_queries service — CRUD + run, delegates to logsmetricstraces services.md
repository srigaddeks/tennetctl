---
source_file: "backend/02_features/05_monitoring/sub_features/04_saved_queries/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.saved_queries service — CRUD + run, delegates to logs/metrics/traces services

## Connections
- [[Logs Service (OTLP ingest + DSL query)]] - `shares_data_with` [EXTRACTED]
- [[Node monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[monitoring.metrics service (register, list, get, increment, set_gauge, observe_histogram, query DSL)]] - `shares_data_with` [EXTRACTED]
- [[monitoring.query_dsl — shared DSL validation and compilation for logs, metrics, traces]] - `calls` [EXTRACTED]
- [[monitoring.saved_queries repository — raw SQL against 10_fct_monitoring_saved_queries  v_monitoring_saved_queries]] - `calls` [EXTRACTED]
- [[monitoring.saved_queries routes — CRUD + run endpoint]] - `calls` [EXTRACTED]
- [[monitoring.traces service — query DSL + OTLP traces publish pipeline]] - `shares_data_with` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation