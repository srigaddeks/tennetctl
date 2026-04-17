---
source_file: "backend/02_features/05_monitoring/query_dsl/compiler.py"
type: "rationale"
community: "Monitoring Query DSL"
location: "L44"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Monitoring_Query_DSL
---

# Raise InvalidQueryError if from_ts is older than the retention window.

## Connections
- [[_check_retention()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Monitoring_Query_DSL