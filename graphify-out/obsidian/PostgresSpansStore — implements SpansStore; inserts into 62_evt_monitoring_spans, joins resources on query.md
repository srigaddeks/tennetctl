---
source_file: "backend/02_features/05_monitoring/stores/postgres_spans_store.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# PostgresSpansStore — implements SpansStore; inserts into 62_evt_monitoring_spans, joins resources on query

## Connections
- [[DB Table 05_monitoring.11_fct_monitoring_resources]] - `calls` [EXTRACTED]
- [[DB Table 05_monitoring.62_evt_monitoring_spans]] - `calls` [EXTRACTED]
- [[SpansStore Protocol — insert_batch, query_by_trace, query interface]] - `implements` [EXTRACTED]
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation