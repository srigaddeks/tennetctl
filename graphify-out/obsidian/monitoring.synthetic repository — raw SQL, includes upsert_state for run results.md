---
source_file: "backend/02_features/05_monitoring/sub_features/06_synthetic/repository.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.synthetic repository — raw SQL, includes upsert_state for run results

## Connections
- [[DB table 05_monitoring.10_fct_monitoring_synthetic_checks]] - `references` [EXTRACTED]
- [[DB table 05_monitoring.20_dtl_monitoring_synthetic_state — upserted after each check run]] - `references` [EXTRACTED]
- [[DB view 05_monitoring.v_monitoring_synthetic_checks]] - `references` [EXTRACTED]
- [[monitoring.synthetic service — CRUD with audit emission via catalog.run_node]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation