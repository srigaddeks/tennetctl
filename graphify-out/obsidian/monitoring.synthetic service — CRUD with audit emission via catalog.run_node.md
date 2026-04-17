---
source_file: "backend/02_features/05_monitoring/sub_features/06_synthetic/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.synthetic service — CRUD with audit emission via catalog.run_node

## Connections
- [[Node audit.events.emit — used by synthetic service for mutation audit events]] - `calls` [EXTRACTED]
- [[Node monitoring.synthetic.create — create synthetic check (kind=effect, emits_audit=True)]] - `conceptually_related_to` [INFERRED]
- [[Node monitoring.synthetic.delete — soft-delete synthetic check (kind=effect, emits_audit=True)]] - `calls` [EXTRACTED]
- [[Node monitoring.synthetic.get — fetch synthetic check by id (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[Node monitoring.synthetic.list — list synthetic checks (kind=request, emits_audit=False)]] - `calls` [EXTRACTED]
- [[Node monitoring.synthetic.update — update synthetic check (kind=effect, emits_audit=True)]] - `calls` [EXTRACTED]
- [[monitoring.synthetic repository — raw SQL, includes upsert_state for run results]] - `calls` [EXTRACTED]
- [[monitoring.synthetic routes — 5-endpoint CRUD at v1monitoringsynthetic-checks]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation