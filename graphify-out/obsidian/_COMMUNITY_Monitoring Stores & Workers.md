---
type: community
cohesion: 0.02
members: 118
---

# Monitoring Stores & Workers

**Cohesion:** 0.02 - loosely connected
**Members:** 118 nodes

## Members
- [[.__init__()_19]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[.__init__()_17]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[.__init__()_3]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[.__init__()_4]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[.__init__()_9]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[.__init__()_15]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[.__init__()_11]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.__init__()_10]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.__init__()_18]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._backoff()]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[._dlq()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[._dlq()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._ensure_subscription()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[._ensure_subscription()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._extract_resource()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._handle_failure()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[._handle_failure()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._loop()_2]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[._loop()]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[._process_batch()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[._process_batch()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[._run_once()]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[._run_proc()]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[._sleep_s_until_0300_utc()]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[._supervised()]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.apply()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[.health()]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.insert_batch()_3]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[.load()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[.maybe_reload()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[.query()_3]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[.query_by_trace()_1]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[.run_once()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[.run_once()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[.set_rules()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[.snapshot()]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.start()_8]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[.start()_6]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[.start()_4]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[.start()_1]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.start()_7]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[.stop()_8]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[.stop()_6]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[.stop()_4]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[.stop()_1]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[.stop()_7]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[.unsubscribe()]] - code - backend/02_features/05_monitoring/workers/notify_listener.py
- [[.upsert()_1]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[Apply all rules. Returns new RedactionResult; input is not mutated.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[Cancel all workers; wait up to ``timeout`` seconds for drain.]] - rationale - backend/02_features/05_monitoring/workers/runner.py
- [[Compile one row from the view into a RedactionRule; None on bad regex.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[Convert OTel AnyValue proto to Python-native.]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[For tests — inject pre-compiled rules without hitting the DB.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[Hash-interned resource records. Idempotent upsert on (org_id, resource_hash).]] - rationale - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[Interned OTel resource identity.]] - rationale - backend/02_features/05_monitoring/stores/types.py
- [[JetStream → Postgres logs consumer.  Pull-subscribes to ``MONITORING_LOGS`` with]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[JetStream → Postgres spans consumer.  Parallel to logs_consumer — drains MONITOR]] - rationale - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[Load rules from DB. Returns number of active rules loaded.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[Log redaction engine.  Loads rules from v_monitoring_redaction_rules; caches com]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[LogQuery]] - code - backend/02_features/05_monitoring/stores/types.py
- [[LogRecord]] - code - backend/02_features/05_monitoring/stores/types.py
- [[LogsConsumer]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[Main loop — exits only on stop() or unhandled exception.]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[MetricDef]] - code - backend/02_features/05_monitoring/stores/types.py
- [[MetricPoint]] - code - backend/02_features/05_monitoring/stores/types.py
- [[On insert failure nack (redeliver) unless max_deliver exhausted.]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[Partition manager — runs monitoring_partition_manager() daily at 0300 UTC.  Als]] - rationale - backend/02_features/05_monitoring/workers/partition_manager.py
- [[PartitionManager]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[Postgres implementation of ResourcesStore — hash-interned service identities.]] - rationale - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[Postgres implementation of SpansStore.]] - rationale - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[PostgresResourcesStore]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[PostgresSpansStore]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[Pull-subscribe consumer draining MONITORING_LOGS into Postgres.]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[Pull-subscribe consumer draining MONITORING_SPANS into Postgres.]] - rationale - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[Pydantic models for the Monitoring Query DSL.  See ADR-029. Security-critical t]] - rationale - backend/02_features/05_monitoring/query_dsl/types.py
- [[RedactionEngine]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[RedactionResult]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[RedactionRule]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[Reload rules if cache TTL has expired.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[ResourceRecord]] - code - backend/02_features/05_monitoring/stores/types.py
- [[Return per-worker health snapshot.]] - rationale - backend/02_features/05_monitoring/workers/runner.py
- [[Return value from apply() — a new LogRecord dict + extra dropped count.]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[Rollup scheduler — calls monitoring_rollup_1m5m1h every 603003600 seconds.]] - rationale - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[RollupScheduler]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[SHA-256 of canonical JSON of the identity tuple. Deterministic.]] - rationale - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[Single fetch cycle. Returns number of messages processed.]] - rationale - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[SpanQuery]] - code - backend/02_features/05_monitoring/stores/types.py
- [[SpanRecord]] - code - backend/02_features/05_monitoring/stores/types.py
- [[SpansConsumer]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[Start supervised workers.          ``js`` may be None when NATS is unavailable —]] - rationale - backend/02_features/05_monitoring/workers/runner.py
- [[Supervises monitoring workers. Designed to be started in FastAPI lifespan.]] - rationale - backend/02_features/05_monitoring/workers/runner.py
- [[Thread-safe (single-process async) redaction engine.      ``load(pool)`` refresh]] - rationale - backend/02_features/05_monitoring/workers/redaction.py
- [[TimeseriesPoint]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[TimeseriesResult]] - code - backend/02_features/05_monitoring/stores/types.py
- [[WorkerPool]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[WorkerState]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[_any_value_to_py()]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_body_to_str()]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_build_log_records()]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_build_span_records()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[_compile_rule()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[_extract_resource()]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_hex()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_hex()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[_kvs_to_dict()]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_nanos_to_dt()_1]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[_nanos_to_dt()]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[compute_resource_hash()]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[logs_consumer.py]] - code - backend/02_features/05_monitoring/workers/logs_consumer.py
- [[partition_manager.py]] - code - backend/02_features/05_monitoring/workers/partition_manager.py
- [[postgres_resources_store.py]] - code - backend/02_features/05_monitoring/stores/postgres_resources_store.py
- [[postgres_spans_store.py]] - code - backend/02_features/05_monitoring/stores/postgres_spans_store.py
- [[redaction.py]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[rollup_scheduler.py]] - code - backend/02_features/05_monitoring/workers/rollup_scheduler.py
- [[rules()]] - code - backend/02_features/05_monitoring/workers/redaction.py
- [[runner.py_1]] - code - backend/02_features/05_monitoring/workers/runner.py
- [[spans_consumer.py]] - code - backend/02_features/05_monitoring/workers/spans_consumer.py
- [[types.py]] - code - backend/02_features/05_monitoring/stores/types.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Stores_&_Workers
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 7 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 6 edges to [[_COMMUNITY_Service & Repository Layer]]
- 5 edges to [[_COMMUNITY_Core Infrastructure]]
- 3 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Auth & Error Handling]]
- 2 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 1 edge to [[_COMMUNITY_Audit Emit Pipeline]]
- 1 edge to [[_COMMUNITY_Observability Instrumentation]]

## Top bridge nodes
- [[.start()_1]] - degree 15, connects to 3 communities
- [[.start()_8]] - degree 7, connects to 2 communities
- [[.upsert()_1]] - degree 6, connects to 2 communities
- [[ResourceRecord]] - degree 6, connects to 2 communities
- [[._dlq()_1]] - degree 5, connects to 2 communities