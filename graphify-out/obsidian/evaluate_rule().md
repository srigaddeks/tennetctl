---
source_file: "backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py"
type: "code"
community: "Monitoring Query DSL"
location: "L62"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Monitoring_Query_DSL
---

# evaluate_rule()

## Connections
- [[._evaluate_one_rule()]] - `calls` [INFERRED]
- [[.run()_30]] - `calls` [INFERRED]
- [[AlertTransition]] - `calls` [EXTRACTED]
- [[Evaluate a single rule. Returns list of transitions to persist.      Idempotent]] - `rationale_for` [EXTRACTED]
- [[ValueError]] - `calls` [INFERRED]
- [[_condition_breached()]] - `calls` [EXTRACTED]
- [[compile_logs_query()]] - `calls` [INFERRED]
- [[compile_metrics_query()]] - `calls` [INFERRED]
- [[evaluate_all_active_rules()]] - `calls` [INFERRED]
- [[evaluator.py]] - `contains` [EXTRACTED]
- [[fingerprint_for()]] - `calls` [EXTRACTED]
- [[get()_1]] - `calls` [INFERRED]
- [[validate_logs_query()]] - `calls` [INFERRED]
- [[validate_metrics_query()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Monitoring_Query_DSL