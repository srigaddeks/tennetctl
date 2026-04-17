---
source_file: "backend/02_features/05_monitoring/sub_features/02_metrics/service.py"
type: "document"
community: "Alert Rules & Evaluation"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Ingest hot-path audit bypass: increment/set_gauge/observe_histogram skip audit on success (mirrors vault secrets.get pattern)

## Connections
- [[Metric cardinality enforcement max_cardinality per metric definition, rejects excess label combinations, emits failure audit]] - `conceptually_related_to` [INFERRED]
- [[monitoring.metrics service (register, list, get, increment, set_gauge, observe_histogram, query DSL)]] - `implements` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation