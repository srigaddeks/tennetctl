---
source_file: "backend/02_features/05_monitoring/stores/types.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Alert_Rules_&_Evaluation
---

# Store Types — frozen dataclasses: ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery

## Connections
- [[LogsStore Protocol — insert_batch + query interface]] - `references` [EXTRACTED]
- [[MetricsStore Protocol — register, increment, set_gauge, observe_histogram, query_timeseries, query_latest]] - `references` [INFERRED]
- [[PostgresLogsStore — implements LogsStore; inserts into 60_evt_monitoring_logs, cursor pagination]] - `references` [INFERRED]
- [[PostgresMetricsStore — implements MetricsStore; cardinality-gated writes into 61_evt_monitoring_metric_points]] - `references` [INFERRED]
- [[PostgresResourcesStore — SHA-256 hash-interned upsert into 11_fct_monitoring_resources]] - `references` [INFERRED]
- [[PostgresSpansStore — implements SpansStore; inserts into 62_evt_monitoring_spans, joins resources on query]] - `references` [INFERRED]
- [[ResourcesStore Protocol — upsert interface for OTel resource identities]] - `references` [INFERRED]
- [[SpansStore Protocol — insert_batch, query_by_trace, query interface]] - `references` [INFERRED]

#graphify/code #graphify/INFERRED #community/Alert_Rules_&_Evaluation