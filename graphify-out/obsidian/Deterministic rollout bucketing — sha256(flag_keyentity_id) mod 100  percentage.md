---
source_file: "backend/02_features/09_featureflags/sub_features/05_evaluations/service.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# Deterministic rollout bucketing — sha256(flag_key:entity_id) mod 100 < percentage

## Connections
- [[featureflags.evaluations service — evaluate(), _eval_condition(), _in_rollout(), scope resolution]] - `implements` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine