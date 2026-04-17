---
source_file: "backend/02_features/09_featureflags/sub_features/05_evaluations/service.py"
type: "rationale"
community: "Feature Flag Evaluations Node"
location: "L221"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluations_Node
---

# Deterministic bucketing: hash(flag_key + entity_id) mod 100 < percentage.

## Connections
- [[_in_rollout()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Feature_Flag_Evaluations_Node