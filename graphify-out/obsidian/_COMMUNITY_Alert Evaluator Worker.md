---
type: community
cohesion: 0.02
members: 119
---

# Alert Evaluator Worker

**Cohesion:** 0.02 - loosely connected
**Members:** 119 nodes

## Members
- [[.__init__()_16]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[.__init__()_14]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[.__init__()_7]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[.__init__()_5]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.__init__()_8]] - code - backend/02_features/05_monitoring/workers/synthetic_runner.py
- [[._check_cardinality()]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[._ctx_for_rule()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._cycle()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._ensure_registered()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[._ensure_resource()]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[._evaluate_one_rule()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._handle_firing()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._handle_resolving()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._handle_transition()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._loop()_1]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._notify()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[._register_metric()]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[._resolve_recipient()]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[.increment()_2]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[.increment()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.invalidate_all()]] - code - backend/02_features/02_vault/client.py
- [[.observe()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[.observe_histogram()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.query_latest()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.query_timeseries()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.register()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.run()_26]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[.scrape_once()]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[.set()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[.set_gauge()_1]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[.start()_5]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[.start()_3]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[.stop()_5]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[.stop()_3]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[.stop()]] - code - backend/02_features/05_monitoring/workers/synthetic_runner.py
- [[30s loop over active alert rules.      Self-metrics       monitoring.alerts.eva]] - rationale - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[APISIX Prometheus scraper.  Every ``scrape_interval_s`` (default 15s) 1. GET ap]] - rationale - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[Alert evaluator worker — periodic loop over active rules.  Runs every ``config.m]] - rationale - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[AlertEvaluatorWorker]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[ApisixScraper]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[Append a checker to the chain. Runs before the default checker.]] - rationale - backend/01_catalog/authz.py
- [[Authorization hook for the node runner (NCP v1 §9).  Runs before every `run_node]] - rationale - backend/01_catalog/authz.py
- [[Clear all custom checkers. For teststeardown.]] - rationale - backend/01_catalog/authz.py
- [[Clear the registry. For testing only.]] - rationale - backend/01_core/node_registry.py
- [[CounterHandle]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[Drop every cache entry. No wire path yet; used by tests + future LISTENNOTIFY.]] - rationale - backend/02_features/02_vault/client.py
- [[Fire a notify.send.transactional call. Returns True on success.]] - rationale - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[GaugeHandle]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[HistogramHandle]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[INSERT a new firing alert event row.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[In-memory node registry — stores NodeContract instances by key.  Nodes are the p]] - rationale - backend/01_core/node_registry.py
- [[In-process metrics SDK — counter  gauge  histogram factories.  Usage     from]] - rationale - backend/02_features/05_monitoring/sdk/metrics.py
- [[Input_26]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[MetricSetRequest]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[NodeContract]] - code - backend/01_core/node_registry.py
- [[Output_26]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[Polls APISIX apisixprometheusmetrics and writes to MetricsStore.]] - rationale - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[Postgres implementation of MetricsStore.  - register ON CONFLICT idempotent on]] - rationale - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[PostgresMetricsStore]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[Process one transition under its own transaction.]] - rationale - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[Register a node contract. Validates key format and kind.]] - rationale - backend/01_core/node_registry.py
- [[Return True if OK to insert; False if over limit.]] - rationale - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[Return all registered node contracts.]] - rationale - backend/01_core/node_registry.py
- [[Return the latest firing event row for (rule_id, fingerprint) or None.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[SetGauge]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[Single scrape. Returns number of samples written. Never raises.]] - rationale - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[Testing hook — drop process-level SDK caches.]] - rationale - backend/02_features/05_monitoring/sdk/metrics.py
- [[Testing hook — drop the process cache.]] - rationale - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[Typed contract for a node in the workflow system.]] - rationale - backend/01_core/node_registry.py
- [[_BaseHandle]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[_cache_clear()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_enabled()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[_now()_1]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[_pool_from_ctx()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[_prom_kind_to_id()]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[_reset_sdk_cache()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[alert_evaluator_worker.py]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[apisix_scraper.py]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[arrayBufferToBase64()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[authz.py]] - code - backend/01_catalog/authz.py
- [[buildCsvUrl()]] - code - frontend/src/app/(dashboard)/audit/page.tsx
- [[buildQueries()]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[clear()]] - code - backend/01_core/node_registry.py
- [[clear_checkers()]] - code - backend/01_catalog/authz.py
- [[counter()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[fetchVapidKey()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[find_firing_event()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[flatten()]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[fmtTime()]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[gauge()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[hashServiceColor()]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[histogram()]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[insert_alert_event()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[isPublic()]] - code - frontend/src/proxy.ts
- [[list_all()]] - code - backend/01_core/node_registry.py
- [[mergeSeries()]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[metrics-chart.tsx]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[metrics.py]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[monitoring.metrics.set_gauge — record a gauge observation.  Effect node, tx=call]] - rationale - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[node_registry.py]] - code - backend/01_core/node_registry.py
- [[notificationPermission()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[onKey()]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[page.tsx_23]] - code - frontend/src/app/(dashboard)/audit/page.tsx
- [[postgres_metrics_store.py]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[proxy()]] - code - frontend/src/proxy.ts
- [[proxy.ts]] - code - frontend/src/proxy.ts
- [[register()]] - code - backend/01_core/node_registry.py
- [[registerSW()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[register_checker()]] - code - backend/01_catalog/authz.py
- [[set_gauge.py]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[trace-waterfall.tsx]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[update_alert_event()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[url()]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[urlBase64ToUint8Array()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[use-webpush.ts]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[useDisableWebPush()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[useEnableWebPush()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[useWebPushSubscriptions()]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[webPushSupported()]] - code - frontend/src/features/notify/hooks/use-webpush.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Alert_Evaluator_Worker
SORT file.name ASC
```

## Connections to other communities
- 37 edges to [[_COMMUNITY_Service & Repository Layer]]
- 8 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 7 edges to [[_COMMUNITY_Monitoring Stores & Workers]]
- 5 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Auth & Error Handling]]
- 3 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 3 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 2 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 2 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 1 edge to [[_COMMUNITY_Frontend API Client]]
- 1 edge to [[_COMMUNITY_Audit Outbox]]
- 1 edge to [[_COMMUNITY_Observability Instrumentation]]
- 1 edge to [[_COMMUNITY_Core Infrastructure]]

## Top bridge nodes
- [[.set()]] - degree 27, connects to 7 communities
- [[.increment()_2]] - degree 10, connects to 3 communities
- [[._evaluate_one_rule()]] - degree 9, connects to 2 communities
- [[._notify()]] - degree 9, connects to 2 communities
- [[clear()]] - degree 9, connects to 2 communities