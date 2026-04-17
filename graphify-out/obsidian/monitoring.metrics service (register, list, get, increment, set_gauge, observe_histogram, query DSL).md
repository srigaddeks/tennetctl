---
source_file: "backend/02_features/05_monitoring/sub_features/02_metrics/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.metrics service (register, list, get, increment, set_gauge, observe_histogram, query DSL)

## Connections
- [[IncrementMetric (monitoring.metrics.increment)]] - `calls` [EXTRACTED]
- [[Ingest hot-path audit bypass incrementset_gaugeobserve_histogram skip audit on success (mirrors vault secrets.get pattern)]] - `implements` [EXTRACTED]
- [[Metric cardinality enforcement max_cardinality per metric definition, rejects excess label combinations, emits failure audit]] - `implements` [EXTRACTED]
- [[MetricsQueryNode (monitoring.metrics.query)]] - `calls` [EXTRACTED]
- [[ObserveHistogram (monitoring.metrics.observe_histogram)]] - `calls` [EXTRACTED]
- [[RegisterMetric (monitoring.metrics.register)]] - `calls` [EXTRACTED]
- [[SetGauge (monitoring.metrics.set_gauge)]] - `calls` [EXTRACTED]
- [[monitoring.metrics FastAPI routes (POST register, GET list, GET one, POST incrementsetobserve, POST query)]] - `calls` [EXTRACTED]
- [[monitoring.metrics repository (v_monitoring_metrics view, delegates ingest to stores layer)]] - `calls` [EXTRACTED]
- [[monitoring.metrics schemas (MetricKind countergaugehistogram, MetricRegisterRequest, IncrementSetObserve requests, MetricResponse)]] - `references` [EXTRACTED]
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - `shares_data_with` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation