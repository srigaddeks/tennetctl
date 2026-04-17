---
source_file: "backend/02_features/05_monitoring/sub_features/07_alerts/evaluator.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Alert Evaluator (for_duration gating + fingerprint dedup)

## Connections
- [[Alert Silence (matcher-based suppression)]] - `conceptually_related_to` [INFERRED]
- [[AlertTransition (firing_new  firing_update  resolving)]] - `implements` [EXTRACTED]
- [[Alerts Service (monitoring.alerts)]] - `calls` [EXTRACTED]
- [[DB 20_dtl_monitoring_rule_state (pending_fingerprints JSONB)]] - `shares_data_with` [EXTRACTED]
- [[EvaluateRule (monitoring.alerts.evaluate)]] - `calls` [EXTRACTED]
- [[Monitoring Query DSL (validate + compile metricslogs)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation