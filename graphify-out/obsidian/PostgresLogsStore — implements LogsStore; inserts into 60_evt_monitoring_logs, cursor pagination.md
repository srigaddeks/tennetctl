---
source_file: "backend/02_features/05_monitoring/stores/postgres_logs_store.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# PostgresLogsStore — implements LogsStore; inserts into 60_evt_monitoring_logs, cursor pagination

## Connections
- [[DB Table 05_monitoring.60_evt_monitoring_logs]] - `calls` [EXTRACTED]
- [[LogsStore Protocol — insert_batch + query interface]] - `implements` [EXTRACTED]
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation