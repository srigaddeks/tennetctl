---
type: community
cohesion: 0.03
members: 124
---

# Alert Rules & Evaluation

**Cohesion:** 0.03 - loosely connected
**Members:** 124 nodes

## Members
- [[Alert Evaluator (for_duration gating + fingerprint dedup)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[Alert Silence (matcher-based suppression)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[AlertTransition (firing_new  firing_update  resolving)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[Alerts Repository (monitoring.alerts)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/repository.py
- [[Alerts Routes (monitoring.alerts)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/routes.py
- [[Alerts Schemas (monitoring.alerts)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/schemas.py
- [[Alerts Service (monitoring.alerts)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[Catalog Node Base Class]] - code - backend/01_catalog/node.py
- [[Counter metric type]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/increment.py
- [[DB Table 05_monitoring.10_fct_monitoring_metrics]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[DB Table 05_monitoring.11_fct_monitoring_resources]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[DB Table 05_monitoring.60_evt_monitoring_logs]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[DB Table 05_monitoring.61_evt_monitoring_metric_points]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[DB Table 05_monitoring.62_evt_monitoring_spans]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[DB table 02_vault.11_fct_vault_configs (plaintext typed configs)]] - document - backend/02_features/02_vault/sub_features/02_configs/repository.py
- [[DB table 04_audit.60_evt_audit (append-only audit events)]] - document - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[DB table 05_monitoring.10_fct_monitoring_saved_queries]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/repository.py
- [[DB table 05_monitoring.10_fct_monitoring_synthetic_checks]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/repository.py
- [[DB table 05_monitoring.20_dtl_monitoring_synthetic_state — upserted after each check run]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/repository.py
- [[DB table 61_evt_audit_outbox (append-only, BIGINT cursor)]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[DB view 02_vault.v_vault_configs (joins scope + value_type codes, pivots description)]] - document - backend/02_features/02_vault/sub_features/02_configs/repository.py
- [[DB view 04_audit.v_audit_events (joins dim_audit_categories + dim_audit_event_keys)]] - document - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[DB view 05_monitoring.v_monitoring_logs — read view for log tail and queries]] - code - backend/02_features/05_monitoring/sub_features/01_logs/repository.py
- [[DB view 05_monitoring.v_monitoring_saved_queries]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/repository.py
- [[DB view 05_monitoring.v_monitoring_synthetic_checks]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/repository.py
- [[DB view v_audit_events]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[DB 12_fct_monitoring_alert_rules]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/repository.py
- [[DB 13_fct_monitoring_silences]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/repository.py
- [[DB 20_dtl_monitoring_rule_state (pending_fingerprints JSONB)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[DB 60_evt_monitoring_alert_events (partitioned)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[EvaluateRule (monitoring.alerts.evaluate)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[EventGet (monitoring.alerts.event_get)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[EventList (monitoring.alerts.event_list)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[Gauge metric type]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[Histogram metric type]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/observe.py
- [[IncrementMetric (monitoring.metrics.increment)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/increment.py
- [[Ingest hot-path audit bypass incrementset_gaugeobserve_histogram skip audit on success (mirrors vault secrets.get pattern)]] - document - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[Logs Service (OTLP ingest + DSL query)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[LogsStore Protocol — insert_batch + query interface]] - code - backend/02_features/05_monitoring/stores/logs_store.py
- [[Metric cardinality enforcement max_cardinality per metric definition, rejects excess label combinations, emits failure audit]] - document - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[MetricsQueryNode (monitoring.metrics.query)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/query.py
- [[MetricsStore Protocol — register, increment, set_gauge, observe_histogram, query_timeseries, query_latest]] - code - backend/02_features/05_monitoring/stores/metrics_store.py
- [[Monitoring Query DSL (validate + compile metricslogs)]] - code - backend/02_features/05_monitoring/query_dsl.py
- [[NATS DLQ subject monitoring.dlq.logs]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[NATS DLQ subject monitoring.dlq.spans]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[NATS JetStream (log publish target)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[NATS JetStream streams for monitoring workqueue retention for logsspans, limits retention for DLQ]] - document - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[NATS JetStream — async message transport for OTLP ingest pipeline]] - code - backend/01_core/nats.py
- [[NATS subject pattern monitoring.logs.otel.{service} — OTLP logs per service]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[NATS subject pattern monitoring.traces.otel.{service} — OTLP traces per service]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[Node audit.events.emit — used by synthetic service for mutation audit events]] - code - backend/02_features/04_audit/sub_features/events/nodes/emit.py
- [[Node monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/otlp_ingest.py
- [[Node monitoring.logs.query — DSL query node (kind=request, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/query.py
- [[Node monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[Node monitoring.synthetic.create — create synthetic check (kind=effect, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[Node monitoring.synthetic.delete — soft-delete synthetic check (kind=effect, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[Node monitoring.synthetic.get — fetch synthetic check by id (kind=request, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[Node monitoring.synthetic.list — list synthetic checks (kind=request, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[Node monitoring.synthetic.update — update synthetic check (kind=effect, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[NotifyListener worker — Postgres LISTENNOTIFY broadcaster for log tail SSE]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[OTLP Logs Decoder (protobufJSON → JetStream batches)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[ObserveHistogram (monitoring.metrics.observe_histogram)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/observe.py
- [[OtlpTracesIngest — node key monitoring.traces.otlp_ingest (request kind)]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[Outbox polling pattern (since_id BIGINT cursor, oldest-first, optional org_id filter)]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[PostgresLogsStore — implements LogsStore; inserts into 60_evt_monitoring_logs, cursor pagination]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[PostgresMetricsStore — implements MetricsStore; cardinality-gated writes into 61_evt_monitoring_metric_points]] - code - backend/02_features/05_monitoring/stores/postgres_metrics_store.py
- [[PostgresResourcesStore — SHA-256 hash-interned upsert into 11_fct_monitoring_resources]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[PostgresSpansStore — implements SpansStore; inserts into 62_evt_monitoring_spans, joins resources on query]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[RegisterMetric (monitoring.metrics.register)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/register.py
- [[ResourcesStore Protocol — upsert interface for OTel resource identities]] - code - backend/02_features/05_monitoring/stores/resources_store.py
- [[RuleCreate (monitoring.alerts.rule_create)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[RuleDelete (monitoring.alerts.rule_delete)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[RuleGet (monitoring.alerts.rule_get)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[RuleList (monitoring.alerts.rule_list)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[RuleUpdate (monitoring.alerts.rule_update)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[SetGauge (monitoring.metrics.set_gauge)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/set_gauge.py
- [[SilenceAdd (monitoring.alerts.silence_add)]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[SpansStore Protocol — insert_batch, query_by_trace, query interface]] - code - backend/02_features/05_monitoring/stores/spans_store.py
- [[Store Types — frozen dataclasses ResourceRecord, LogRecord, LogQuery, MetricDef, MetricPoint, TimeseriesPoint, TimeseriesResult, SpanRecord, SpanQuery]] - code - backend/02_features/05_monitoring/stores/types.py
- [[Traces Repository (empty — writes delegated to 13-04 consumer)]] - code - backend/02_features/05_monitoring/sub_features/03_traces/repository.py
- [[Traces Routes — OTLPHTTP receiver + DSL query endpoints]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[TracesQueryNode — node key monitoring.traces.query (request kind)]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[audit feature router (aggregates events + saved_views sub-routers)]] - code - backend/02_features/04_audit/routes.py
- [[audit outbox service (current_cursor, poll)]] - code - backend/02_features/04_audit/sub_features/03_outbox/service.py
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - code - backend/02_features/04_audit/sub_features/01_events/routes.py
- [[audit.events Pydantic schemas (AuditEventFilter, AuditEventRow, FunnelRequest, RetentionResponse)]] - code - backend/02_features/04_audit/sub_features/01_events/schemas.py
- [[audit.events asyncpg repository (cursor pagination, stats, funnel, retention, upsert_event_key)]] - code - backend/02_features/04_audit/sub_features/01_events/repository.py
- [[audit.events service (read path query, get, stats, funnel, retention, list_keys)]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[audit.outbox schemas (AuditEventRowSlim, AuditTailResponse, AuditOutboxCursorResponse)]] - code - backend/02_features/04_audit/sub_features/03_outbox/schemas.py
- [[audit.outbox.repository — poll_outbox, latest_outbox_id (used by notify worker)]] - code - backend/02_features/04_audit/sub_features/03_outbox/repository.py
- [[audit.saved_views Pydantic schemas (AuditSavedViewCreate, AuditSavedViewRow)]] - code - backend/02_features/04_audit/sub_features/02_saved_views/schemas.py
- [[audit.saved_views service (listcreatedelete saved views)]] - code - backend/02_features/04_audit/sub_features/02_saved_views/service.py
- [[core nats (JetStream client singleton, backoff retry)]] - code - backend/01_core/nats.py
- [[monitoring JetStream bootstrap (MONITORING_LOGS 72h2GB, MONITORING_SPANS 24h4GB, MONITORING_DLQ 7d1GB — idempotent createupdate)]] - code - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[monitoring admin + health routes — worker pool health, DLQ replay (lives in saved_queries package)]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[monitoring feature router (aggregates logs, traces, metrics, saved_queries, dashboards, synthetic, alerts sub-routers)]] - code - backend/02_features/05_monitoring/routes.py
- [[monitoring.logs routes — OTLP ingest + query + SSE live-tail]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[monitoring.metrics FastAPI routes (POST register, GET list, GET one, POST incrementsetobserve, POST query)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/routes.py
- [[monitoring.metrics repository (v_monitoring_metrics view, delegates ingest to stores layer)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[monitoring.metrics schemas (MetricKind countergaugehistogram, MetricRegisterRequest, IncrementSetObserve requests, MetricResponse)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[monitoring.metrics service (register, list, get, increment, set_gauge, observe_histogram, query DSL)]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[monitoring.query_dsl — shared DSL validation and compilation for logs, metrics, traces]] - code - backend/02_features/05_monitoring/query_dsl.py
- [[monitoring.saved_queries Pydantic schemas — SavedQueryCreateRequest, SavedQueryUpdateRequest, SavedQueryResponse]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/schemas.py
- [[monitoring.saved_queries repository — raw SQL against 10_fct_monitoring_saved_queries  v_monitoring_saved_queries]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/repository.py
- [[monitoring.saved_queries routes — CRUD + run endpoint]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/routes.py
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/service.py
- [[monitoring.synthetic Pydantic schemas — SyntheticCheckCreateRequest, SyntheticCheckUpdateRequest, SyntheticCheckResponse]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/schemas.py
- [[monitoring.synthetic repository — raw SQL, includes upsert_state for run results]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/repository.py
- [[monitoring.synthetic routes — 5-endpoint CRUD at v1monitoringsynthetic-checks]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/routes.py
- [[monitoring.synthetic service — CRUD with audit emission via catalog.run_node]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/service.py
- [[monitoring.traces OTLP decoder — decodes ExportTraceServiceRequest, routes per ResourceSpans to JetStream subject]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[monitoring.traces service — query DSL + OTLP traces publish pipeline]] - code - backend/02_features/05_monitoring/sub_features/03_traces/service.py
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[node audit.events.query (control node — read-only cursor-paginated event lookup)]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[node audit.events.subscribe (control node — polling outbox consumer)]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py
- [[node vault.configs.create (effect node — create plaintext typed config)]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[node vault.configs.delete (effect node — soft-delete config by id)]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_delete.py
- [[node vault.configs.get (control node — cross-sub-feature config lookup)]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_get.py
- [[node vault.configs.update (effect node — PATCH valuedescriptionis_active)]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_update.py
- [[vault feature router (aggregates secrets + configs sub-routers)]] - code - backend/02_features/02_vault/routes.py
- [[vault.configs FastAPI routes (v1vault-configs, 5 endpoints)]] - code - backend/02_features/02_vault/sub_features/02_configs/routes.py
- [[vault.configs Pydantic schemas (ConfigCreate, ConfigUpdate, ConfigMeta)]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[vault.configs asyncpg repository (reads v_vault_configs, writes fct_vault_configs)]] - code - backend/02_features/02_vault/sub_features/02_configs/repository.py
- [[vault.configs service (createlistgetupdatedelete config)]] - code - backend/02_features/02_vault/sub_features/02_configs/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Alert_Rules_&_Evaluation
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_API Keys Sub-feature]]
- 1 edge to [[_COMMUNITY_Error Types & Authorization]]

## Top bridge nodes
- [[vault.configs service (createlistgetupdatedelete config)]] - degree 9, connects to 1 community
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - degree 7, connects to 1 community
- [[audit.outbox.repository — poll_outbox, latest_outbox_id (used by notify worker)]] - degree 7, connects to 1 community
- [[NATS JetStream (log publish target)]] - degree 6, connects to 1 community