---
source_file: "backend/01_catalog/node.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# Catalog Node Base Class

## Connections
- [[EvaluateRule (monitoring.alerts.evaluate)]] - `implements` [EXTRACTED]
- [[EventGet (monitoring.alerts.event_get)]] - `implements` [EXTRACTED]
- [[EventList (monitoring.alerts.event_list)]] - `implements` [EXTRACTED]
- [[IncrementMetric (monitoring.metrics.increment)]] - `implements` [EXTRACTED]
- [[MetricsQueryNode (monitoring.metrics.query)]] - `implements` [EXTRACTED]
- [[Node monitoring.logs.otlp_ingest — OTLP logs ingest effect node (kind=request, emits_audit=False)]] - `implements` [EXTRACTED]
- [[Node monitoring.logs.query — DSL query node (kind=request, emits_audit=False)]] - `implements` [EXTRACTED]
- [[Node monitoring.saved_queries.run — load and execute a saved DSL (kind=request, emits_audit=False)]] - `implements` [EXTRACTED]
- [[Node monitoring.synthetic.create — create synthetic check (kind=effect, emits_audit=True)]] - `implements` [EXTRACTED]
- [[Node monitoring.synthetic.delete — soft-delete synthetic check (kind=effect, emits_audit=True)]] - `implements` [EXTRACTED]
- [[Node monitoring.synthetic.get — fetch synthetic check by id (kind=request, emits_audit=False)]] - `implements` [EXTRACTED]
- [[Node monitoring.synthetic.list — list synthetic checks (kind=request, emits_audit=False)]] - `implements` [EXTRACTED]
- [[Node monitoring.synthetic.update — update synthetic check (kind=effect, emits_audit=True)]] - `implements` [EXTRACTED]
- [[ObserveHistogram (monitoring.metrics.observe_histogram)]] - `implements` [EXTRACTED]
- [[RegisterMetric (monitoring.metrics.register)]] - `implements` [EXTRACTED]
- [[RuleCreate (monitoring.alerts.rule_create)]] - `implements` [EXTRACTED]
- [[RuleDelete (monitoring.alerts.rule_delete)]] - `implements` [EXTRACTED]
- [[RuleGet (monitoring.alerts.rule_get)]] - `implements` [EXTRACTED]
- [[RuleList (monitoring.alerts.rule_list)]] - `implements` [EXTRACTED]
- [[RuleUpdate (monitoring.alerts.rule_update)]] - `implements` [EXTRACTED]
- [[SetGauge (monitoring.metrics.set_gauge)]] - `implements` [EXTRACTED]
- [[SilenceAdd (monitoring.alerts.silence_add)]] - `implements` [EXTRACTED]
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - `implements` [EXTRACTED]
- [[node audit.events.query (control node — read-only cursor-paginated event lookup)]] - `implements` [EXTRACTED]
- [[node audit.events.subscribe (control node — polling outbox consumer)]] - `implements` [EXTRACTED]
- [[node vault.configs.create (effect node — create plaintext typed config)]] - `implements` [EXTRACTED]
- [[node vault.configs.delete (effect node — soft-delete config by id)]] - `implements` [EXTRACTED]
- [[node vault.configs.get (control node — cross-sub-feature config lookup)]] - `implements` [EXTRACTED]
- [[node vault.configs.update (effect node — PATCH valuedescriptionis_active)]] - `implements` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation