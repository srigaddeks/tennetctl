---
type: community
cohesion: 0.02
members: 164
---

# Monitoring Query DSL

**Cohesion:** 0.02 - loosely connected
**Members:** 164 nodes

## Members
- [[.resolve()]] - code - backend/02_features/05_monitoring/query_dsl/types.py
- [[.run()_42]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[.run()_49]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[.run()_43]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[.run()_30]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[.run()_35]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[.run()_28]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[.run()_40]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[.run()_44]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[.run()_37]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/query.py
- [[.run()_23]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/query.py
- [[.run()_45]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[.run()_31]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[.run()_34]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[.run()_29]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[.run()_33]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[.run()_36]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[.run()_39]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[.run()_2]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[.run()_32]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[.run()_41]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[Alert evaluator — for_duration gating, fingerprint dedup, transition detection.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[AlertTransition]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[Compile a Filter tree into a parameterized SQL WHERE fragment.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[Compile a metrics timeseries query against ``evt_monitoring_metric_points``.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[CreateDashboard]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[CreateSyntheticCheck]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[Decode a cursor token back into ``(recorded_at, id)`` or ``None``.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[DeleteSyntheticCheck]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[Dry-run validation of rule DSL via 13-05 validator.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/service.py
- [[Encode a cursor row ``{recorded_at, id}`` into an opaque base64 token.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[Evaluate a single rule. Returns list of transitions to persist.      Idempotent]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[EvaluateRule]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[EventGet]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[EventList]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[Exposed for tests — deterministic sha256 over (rule_id, sorted labels).]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[GetSyntheticCheck]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[Input_41]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[Input_46]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[Input_42]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[Input_30]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[Input_35]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[Input_28]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[Input_39]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[Input_43]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[Input_23]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[Input_31]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[Input_34]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[Input_29]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[Input_33]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[Input_36]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[Input_38]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[Input_2]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[Input_32]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[Input_40]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[InvalidQueryError]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[ListSyntheticChecks]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[LogsQueryNode]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/query.py
- [[MetricsQueryNode]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/query.py
- [[Monitoring Query DSL compiler.  Produces ``(sql, params)`` tuples for asyncpg. C]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[Monitoring Query DSL — defensive validator.  The Pydantic models in ``types.py``]] - rationale - backend/02_features/05_monitoring/query_dsl/validator.py
- [[Node_1]] - code
- [[Output_41]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[Output_46]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[Output_42]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[Output_30]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[Output_35]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[Output_28]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[Output_39]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[Output_43]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[Output_23]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[Output_31]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[Output_34]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[Output_29]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[Output_33]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[Output_36]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[Output_38]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[Output_2]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[Output_32]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[Output_40]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[Raise InvalidQueryError if from_ts is older than the retention window.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[Raised when a DSL query fails validation.]] - rationale - backend/02_features/05_monitoring/query_dsl/validator.py
- [[Return absolute (from_ts, to_ts). Naive UTC datetimes.]] - rationale - backend/02_features/05_monitoring/query_dsl/types.py
- [[Return all spans for a single trace_id, scoped by context org.]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[RuleCreate]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[RuleDelete]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[RuleGet]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[RuleList]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[RuleUpdate]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[RunSavedQuery]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[SendTransactional]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[SilenceAdd]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[TracesQueryNode]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[Translate user field name to a safe SQL column expression.      Supports JSONB s]] - rationale - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[UpdateSyntheticCheck]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[Validate + compile + execute a logs DSL query. Returns (rows, next_cursor).]] - rationale - backend/02_features/05_monitoring/sub_features/01_logs/service.py
- [[Validate + compile + execute a metrics timeseries DSL query.]] - rationale - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_bind()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_check_retention()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_condition_breached()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[_ctx_org()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_ctx_ws()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_depth_check()]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[_filter_depth()]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[_iso()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_resolve_field()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[_validate_dsl()]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/service.py
- [[compile_filter()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_logs_query()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_metrics_query()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_trace_detail()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compile_traces_query()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[compiler.py]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[create_check.py]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[create_dashboard.py]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[decode_cursor()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[delete_check.py]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[encode_cursor()]] - code - backend/02_features/05_monitoring/query_dsl/compiler.py
- [[evaluate.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[evaluate_rule()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[evaluator.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[event_get.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[event_list.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[fingerprint_for()]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py
- [[get_check.py]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[get_trace()]] - code - backend/02_features/05_monitoring/sub_features/03_traces/service.py
- [[list_alert_events()_1]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/repository.py
- [[list_checks.py]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[monitoring.alerts.evaluate — run a single rule's evaluator cycle.  Effect node e]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/evaluate.py
- [[monitoring.alerts.event_get — fetch one alert event by id + started_at.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_get.py
- [[monitoring.alerts.event_list — list alert events for the caller's org.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/event_list.py
- [[monitoring.alerts.rule_create — create an alert rule.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[monitoring.alerts.rule_delete — soft-delete an alert rule.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[monitoring.alerts.rule_get — fetch an alert rule.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[monitoring.alerts.rule_list — list alert rules for the caller's org.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[monitoring.alerts.rule_update — update an alert rule.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[monitoring.alerts.silence_add — create a silence window.]] - rationale - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[monitoring.dashboards.create — create a dashboard.]] - rationale - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[monitoring.saved_queries.run — load a saved DSL and execute it.]] - rationale - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[monitoring.synthetic.create — create a synthetic check.]] - rationale - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/create_check.py
- [[monitoring.synthetic.delete — soft-delete a synthetic check.]] - rationale - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/delete_check.py
- [[monitoring.synthetic.get — fetch a synthetic check by id.]] - rationale - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/get_check.py
- [[monitoring.synthetic.list — list synthetic checks for the caller's org.]] - rationale - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/list_checks.py
- [[monitoring.synthetic.update — update a synthetic check.]] - rationale - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[monitoring.traces.query — DSL traces query node.]] - rationale - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[notify.send.transactional — Effect node for direct transactional delivery.  Crea]] - rationale - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[query()]] - code - backend/02_features/04_audit/sub_features/01_events/service.py
- [[query.py_1]] - code - backend/02_features/05_monitoring/sub_features/01_logs/nodes/query.py
- [[query.py]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/nodes/query.py
- [[query.py_2]] - code - backend/02_features/05_monitoring/sub_features/03_traces/nodes/query.py
- [[rule_create.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_create.py
- [[rule_delete.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_delete.py
- [[rule_get.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_get.py
- [[rule_list.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_list.py
- [[rule_update.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/rule_update.py
- [[run_saved_query.py]] - code - backend/02_features/05_monitoring/sub_features/04_saved_queries/nodes/run_saved_query.py
- [[send_transactional.py]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[service.py_29]] - code - backend/02_features/05_monitoring/sub_features/03_traces/service.py
- [[silence_add.py]] - code - backend/02_features/05_monitoring/sub_features/07_alerts/nodes/silence_add.py
- [[update_check.py]] - code - backend/02_features/05_monitoring/sub_features/06_synthetic/nodes/update_check.py
- [[validate_logs_query()]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[validate_metrics_query()]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[validate_traces_query()]] - code - backend/02_features/05_monitoring/query_dsl/validator.py
- [[validator.py]] - code - backend/02_features/05_monitoring/query_dsl/validator.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Monitoring_Query_DSL
SORT file.name ASC
```

## Connections to other communities
- 40 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 40 edges to [[_COMMUNITY_Service & Repository Layer]]
- 8 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 5 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 4 edges to [[_COMMUNITY_Monitoring Dashboards Backend]]
- 3 edges to [[_COMMUNITY_Auth & Error Handling]]
- 3 edges to [[_COMMUNITY_Audit Events & Saved Views]]
- 3 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 2 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 1 edge to [[_COMMUNITY_Core Infrastructure]]
- 1 edge to [[_COMMUNITY_Notify Templates & Email Delivery]]

## Top bridge nodes
- [[Node_1]] - degree 31, connects to 5 communities
- [[query()]] - degree 23, connects to 5 communities
- [[evaluate_rule()]] - degree 14, connects to 3 communities
- [[.resolve()]] - degree 8, connects to 3 communities
- [[_validate_dsl()]] - degree 12, connects to 2 communities