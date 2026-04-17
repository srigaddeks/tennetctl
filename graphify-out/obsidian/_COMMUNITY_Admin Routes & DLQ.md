---
type: community
cohesion: 0.03
members: 108
---

# Admin Routes & DLQ

**Cohesion:** 0.03 - loosely connected
**Members:** 108 nodes

## Members
- [[.__init__()_6]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[.__init__()_12]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.__init__()_13]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[._on_notify()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[._run()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.dispatch()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[.publish()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.run()_38]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/otlp_ingest.py
- [[.run()_46]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[.start()_2]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.stop()_2]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.subscribe()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[Async generator that yields SSE-formatted events.      Polls v_monitoring_logs f]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[Attach query loggers to all current + future pool connections.      asyncpg.Pool]] - rationale - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[Block startup when any TENNETCTL_ env var looks like a secret outside the allow]] - rationale - backend/01_core/config.py
- [[Broadcaster]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[Build ExportLogsServiceResponse matching the request content-type.]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[Config]] - code - backend/01_core/config.py
- [[Consume up to ``limit`` messages from the named DLQ and republish them     to th]] - rationale - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[Cross-cutting admin + health routes for monitoring.  - GET healthmonitoring —]] - rationale - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[DLQReplayRequest]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[Decode an OTLPHTTP logs body.      Returns (batches, rejected_count). ``batches]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[Decode an OTLPHTTP traces body.      Returns (batches, rejected_count).]] - rationale - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[Decode and publish each ResourceSpans to JetStream.]] - rationale - backend/02_features/05_monitoring/sub_features/03_traces/service.py
- [[Decode body, publish every ResourceLogs to JetStream.      Returns (published_co]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[Emit a server-kind span per request. Skips infra paths.]] - rationale - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[Fan-out queue broadcaster with drop-oldest policy.]] - rationale - backend/02_features/05_monitoring/workers/notify_listener.py
- [[FastAPI middleware — emit server-kind spans + latency histograms.  Every inbound]] - rationale - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[Input_37]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[LISTENNOTIFY worker — bridges Postgres NOTIFY to SSE broadcasters.  Holds a ded]] - rationale - backend/02_features/05_monitoring/workers/notify_listener.py
- [[LISTENNOTIFY-backed tail generator.      Subscribes to the NotifyListener broad]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[Load configuration from environment variables with sensible defaults.]] - rationale - backend/01_core/config.py
- [[Lowercase and replace any char outside a-z0-9._- with ``-``.]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[MonitoringMiddleware]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[NotifyListener]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[OTLP traces decoder.  Mirror of the logs decoder. Each ResourceSpans becomes one]] - rationale - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[OTLPHTTP logs ingest endpoint.]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[OtlpLogsIngest]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/otlp_ingest.py
- [[OtlpTracesIngest]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[Output_37]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[Parse W3C traceparent. Returns (trace_id_bytes, parent_span_id_bytes) or None.]] - rationale - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[Publish a span to JetStream. Silent-drop on failure.]] - rationale - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[Pull service.name from the ResourceLogs' resource attributes.]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[Register the middleware on the FastAPI app (last — measures everything).]] - rationale - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[Register the query logger on a freshly acquired connection.]] - rationale - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[Replace string and numeric literals with ```` and truncate.]] - rationale - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[Return an asyncpg query-logger callback.      asyncpg's `conn.add_query_logger`]] - rationale - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[Return worker-pool + NATS + store snapshot.]] - rationale - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[SSE live-tail of monitoring logs, scoped to ctx.org_id.      If the NotifyListen]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[Scope gate. The full scope system lands later; for now require the     ``monitor]] - rationale - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[Stub bearer auth when flag enabled, require a bearer token header.      Full va]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[TennetCTL configuration — loads from environment variables.  Config is a frozen]] - rationale - backend/01_core/config.py
- [[_attach_to_conn()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[_build_query_ctx()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[_build_query_span()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[_build_response()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[_build_span_proto()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_check_auth()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[_decode_filter()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[_enforce_env_contract()]] - code - backend/01_core/config.py
- [[_extract_service_name()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[_kv_int()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[_kv_int()_1]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_kv_str()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[_kv_str()_1]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_new_span_id()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_new_trace_id()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_notify_tail_generator()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[_parse_traceparent()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_publish_query_span()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[_publish_span()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_require_admin()]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[_should_skip()]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[_slugify_service_name()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[_tail_generator()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[admin_routes.py]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[asyncpg query instrumentation.  Wraps the pool's connect setup so every new conn]] - rationale - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[asyncpg.py]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[config.py]] - code - backend/01_core/config.py
- [[decode_logs()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[decode_traces()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[dlq_replay()]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[fastapi.py]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[get_js()]] - code - backend/01_core/nats.py
- [[install()_1]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[install()_2]] - code - backend/02_features/05_monitoring/instrumentation/fastapi.py
- [[load_config()]] - code - backend/01_core/config.py
- [[logs_query_route()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[logs_tail_route()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[make_query_logger()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[monitoring.traces.otlp_ingest — effect node for OTLP traces ingest.]] - rationale - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[monitoring_health()]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/admin_routes.py
- [[notify_listener.py]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[otlp_decoder.py]] - code - backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py
- [[otlp_decoder.py_1]] - code - backend/02_features/05_monitoring/sub_features/03_traces/otlp_decoder.py
- [[otlp_ingest.py]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/otlp_ingest.py
- [[otlp_ingest.py_1]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/otlp_ingest.py
- [[otlp_logs()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[otlp_traces()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[publish_logs_batch()]] - code - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[publish_traces_batch()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/service.py
- [[redact_sql()]] - code - backend/02_features/05_monitoring/instrumentation/asyncpg.py
- [[routes.py_30]] - code - backend/02_features/05_monitoring/sub_features/01_logs/routes.py
- [[routes.py_33]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[service.py_26]] - code - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[subscriber_count()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[trace_detail_route()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py
- [[traces_query_route()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/routes.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Admin_Routes_&_DLQ
SORT file.name ASC
```

## Connections to other communities
- 14 edges to [[_COMMUNITY_Service & Repository Layer]]
- 8 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 7 edges to [[_COMMUNITY_Core Infrastructure]]
- 7 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 7 edges to [[_COMMUNITY_Auth & Error Handling]]
- 7 edges to [[_COMMUNITY_Monitoring Stores & Workers]]
- 3 edges to [[_COMMUNITY_Observability Instrumentation]]
- 3 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 1 edge to [[_COMMUNITY_Monitoring Dashboards Backend]]
- 1 edge to [[_COMMUNITY_Session Auth & Middleware]]

## Top bridge nodes
- [[load_config()]] - degree 12, connects to 4 communities
- [[.dispatch()]] - degree 9, connects to 3 communities
- [[_tail_generator()]] - degree 6, connects to 3 communities
- [[logs_query_route()]] - degree 5, connects to 3 communities
- [[traces_query_route()]] - degree 5, connects to 3 communities