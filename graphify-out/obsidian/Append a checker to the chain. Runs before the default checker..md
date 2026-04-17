---
source_file: "backend/01_catalog/authz.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L26"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Append a checker to the chain. Runs before the default checker.

## Connections
- [[register_checker()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker