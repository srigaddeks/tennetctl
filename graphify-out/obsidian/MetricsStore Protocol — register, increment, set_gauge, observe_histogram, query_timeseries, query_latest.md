---
source_file: "backend/02_features/05_monitoring/stores/metrics_store.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# MetricsStore Protocol — register, increment, set_gauge, observe_histogram, query_timeseries, query_latest

## Connections
- [[PostgresMetricsStore — implements MetricsStore; cardinality-gated writes into 61_evt_monitoring_metric_points]] - `implements` [EXTRACTED]
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation