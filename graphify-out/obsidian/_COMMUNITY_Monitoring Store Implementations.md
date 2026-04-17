---
type: community
cohesion: 0.08
members: 24
---

# Monitoring Store Implementations

**Cohesion:** 0.08 - loosely connected
**Members:** 24 nodes

## Members
- [[.increment()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.insert_batch()]] - code - backend/02_features/05_monitoring/stores/logs_store.py
- [[.insert_batch()_2]] - code - backend/02_features/05_monitoring/stores/spans_store.py
- [[.observe_histogram()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.query()]] - code - backend/02_features/05_monitoring/stores/logs_store.py
- [[.query()_2]] - code - backend/02_features/05_monitoring/stores/spans_store.py
- [[.query_by_trace()]] - code - backend/02_features/05_monitoring/stores/spans_store.py
- [[.query_latest()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.query_timeseries()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.register()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.set_gauge()]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[.upsert()]] - code - backend/02_features/05_monitoring/stores/resources_store.py
- [[LogsStore]] - code - backend/02_features/05_monitoring/stores/logs_store.py
- [[Metrics store Protocol.]] - rationale - backend/02_features/05_monitoring/stores/metrics_store.py
- [[MetricsStore]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[Protocol]] - code
- [[Resources store Protocol — interns OTel resource identities.]] - rationale - backend/02_features/05_monitoring/stores/resources_store.py
- [[ResourcesStore]] - code - backend/02_features/05_monitoring/stores/resources_store.py
- [[Spans store Protocol.]] - rationale - backend/02_features/05_monitoring/stores/spans_store.py
- [[SpansStore]] - code - backend/02_features/05_monitoring/stores/spans_store.py
- [[logs_store.py]] - code - backend/02_features/05_monitoring/stores/logs_store.py
- [[metrics_store.py]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[resources_store.py]] - code - backend/02_features/05_monitoring/stores/resources_store.py
- [[spans_store.py]] - code - backend/02_features/05_monitoring/stores/spans_store.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Store_Implementations
SORT file.name ASC
```
