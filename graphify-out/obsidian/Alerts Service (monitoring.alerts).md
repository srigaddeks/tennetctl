---
source_file: "backend/02_features/05_monitoring/sub_features/07_alerts/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Alerts Service (monitoring.alerts)

## Connections
- [[Alert Evaluator (for_duration gating + fingerprint dedup)]] - `calls` [EXTRACTED]
- [[Alerts Repository (monitoring.alerts)]] - `calls` [EXTRACTED]
- [[Alerts Routes (monitoring.alerts)]] - `calls` [EXTRACTED]
- [[DB 20_dtl_monitoring_rule_state (pending_fingerprints JSONB)]] - `shares_data_with` [EXTRACTED]
- [[DB 60_evt_monitoring_alert_events (partitioned)]] - `shares_data_with` [EXTRACTED]
- [[EventGet (monitoring.alerts.event_get)]] - `calls` [EXTRACTED]
- [[EventList (monitoring.alerts.event_list)]] - `calls` [EXTRACTED]
- [[Monitoring Query DSL (validate + compile metricslogs)]] - `calls` [EXTRACTED]
- [[RuleCreate (monitoring.alerts.rule_create)]] - `calls` [EXTRACTED]
- [[RuleDelete (monitoring.alerts.rule_delete)]] - `calls` [EXTRACTED]
- [[RuleGet (monitoring.alerts.rule_get)]] - `calls` [EXTRACTED]
- [[RuleList (monitoring.alerts.rule_list)]] - `calls` [EXTRACTED]
- [[RuleUpdate (monitoring.alerts.rule_update)]] - `calls` [EXTRACTED]
- [[SilenceAdd (monitoring.alerts.silence_add)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation