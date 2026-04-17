---
source_file: "backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.metrics schemas (MetricKind counter/gauge/histogram, MetricRegisterRequest, Increment/Set/Observe requests, MetricResponse)

## Connections
- [[IncrementMetric (monitoring.metrics.increment)]] - `references` [EXTRACTED]
- [[ObserveHistogram (monitoring.metrics.observe_histogram)]] - `references` [EXTRACTED]
- [[RegisterMetric (monitoring.metrics.register)]] - `references` [EXTRACTED]
- [[SetGauge (monitoring.metrics.set_gauge)]] - `references` [EXTRACTED]
- [[monitoring.metrics FastAPI routes (POST register, GET list, GET one, POST incrementsetobserve, POST query)]] - `references` [EXTRACTED]
- [[monitoring.metrics service (register, list, get, increment, set_gauge, observe_histogram, query DSL)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation