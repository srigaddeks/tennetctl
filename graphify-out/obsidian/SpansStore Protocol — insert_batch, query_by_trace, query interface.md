---
source_file: "backend/02_features/05_monitoring/stores/spans_store.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Alert_Rules_&_Evaluation
---

# SpansStore Protocol — insert_batch, query_by_trace, query interface

## Connections
- [[PostgresSpansStore — implements SpansStore; inserts into 62_evt_monitoring_spans, joins resources on query]] - `implements` [EXTRACTED]
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - `references` [INFERRED]
- [[Traces Repository (empty — writes delegated to 13-04 consumer)]] - `conceptually_related_to` [INFERRED]
- [[TracesQueryNode — node key monitoring.traces.query (request kind)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/INFERRED #community/Alert_Rules_&_Evaluation