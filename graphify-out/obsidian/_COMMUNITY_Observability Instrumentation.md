---
type: community
cohesion: 0.04
members: 67
---

# Observability Instrumentation

**Cohesion:** 0.04 - loosely connected
**Members:** 67 nodes

## Members
- [[.emit()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[Add the bridge handler to the root logger. Idempotent.]] - rationale - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[ApisixScraper_1]] - code - backend/02_features/05_monitoring/workers/apisix_scraper.py
- [[Bridge stdlib log records to JetStream via OTLP LogRecord protobuf.]] - rationale - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[Broadcaster (fan-out queue)]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[DB table 61_evt_monitoring_metric_points]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[DB view v_monitoring_logs]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[DB view v_monitoring_redaction_rules]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[DB view v_monitoring_spans]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[Filter (DSL tree)]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[InvalidQueryError_1]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[JetStream subject monitoring.logs.otel.]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[JetStream subject monitoring.traces.otel.]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[LogsConsumer_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[LogsQuery_1]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[MetricsQuery_1]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[MonitoringLogHandler]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[MonitoringMiddleware_1]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[NotifyListener_1]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[PartitionManager_1]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[Postgres NOTIFY channel monitoring_logs_new]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[ReasonBadge()]] - code - frontend/src/app/(dashboard)/feature-flags/evaluate/page.tsx
- [[RedactionEngine_1]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[RedactionRule_1]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[Remove handler + reset flags. Tests only.]] - rationale - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[Return the current in-proc drop counter (for testsintrospection).]] - rationale - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[RollupScheduler_1]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[SpansConsumer_1]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[Stdlib logging → OTLP LogRecord bridge.  Installs a ``logging.Handler`` on the r]] - rationale - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[Timerange_1]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[TracesQuery_1]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[WorkerPool supervisor]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[WorkerState_1]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[_build_log_payload()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[_guarded_publish()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[_publish()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[_reset_for_tests()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[asyncpg instrumentation install()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[compile_filter()_1]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_logs_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_metrics_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_traces_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[cursor encodedecode]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[fastapi instrumentation install()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[getCurrent()]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[get_drop_count()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[gridKey()]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[handleClose()]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[install()]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[isLocked()]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[monitoring SDK metrics module]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[onDelete()]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[onSubmit()]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[page.tsx_25]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[page.tsx_14]] - code - frontend/src/app/(dashboard)/feature-flags/evaluate/page.tsx
- [[page.tsx_15]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[page.tsx_16]] - code - frontend/src/app/(dashboard)/iam/roles/page.tsx
- [[page.tsx_21]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[page.tsx_18]] - code - frontend/src/app/(dashboard)/iam/workspaces/page.tsx
- [[page.tsx_7]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[redact_sql()_1]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[reset()]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[structlog_bridge.py]] - code - backend/02_features/05_monitoring/instrumentation/structlog_bridge.py
- [[toggle()]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[validate_logs_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[validate_metrics_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[validate_traces_query()_1]] - code - backend/02_features/05_monitoring/query_dsl/validator.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Observability_Instrumentation
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Service & Repository Layer]]
- 3 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 2 edges to [[_COMMUNITY_API Keys Sub-feature]]
- 1 edge to [[_COMMUNITY_Frontend API Client]]
- 1 edge to [[_COMMUNITY_Monitoring Stores & Workers]]
- 1 edge to [[_COMMUNITY_Alert Evaluator Worker]]

## Top bridge nodes
- [[.emit()]] - degree 7, connects to 2 communities
- [[_build_log_payload()]] - degree 4, connects to 2 communities
- [[WorkerPool supervisor]] - degree 10, connects to 1 community
- [[reset()]] - degree 6, connects to 1 community
- [[_publish()]] - degree 5, connects to 1 community