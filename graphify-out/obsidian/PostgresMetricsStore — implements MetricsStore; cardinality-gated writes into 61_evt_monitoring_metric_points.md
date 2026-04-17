---
source_file: "backend/02_features/05_monitoring/stores/postgres_metrics_store.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# PostgresMetricsStore — implements MetricsStore; cardinality-gated writes into 61_evt_monitoring_metric_points

## Connections
- [[DB Table 05_monitoring.10_fct_monitoring_metrics]] - `calls` [EXTRACTED]
- [[DB Table 05_monitoring.61_evt_monitoring_metric_points]] - `calls` [EXTRACTED]
- [[MetricsStore Protocol — register, increment, set_gauge, observe_histogram, query_timeseries, query_latest]] - `implements` [EXTRACTED]
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation