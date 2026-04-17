---
source_file: "backend/02_features/09_featureflags/sub_features/05_evaluations/service.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# Flag evaluation pipeline: scope resolution → overrides → rules → env default → flag default

## Connections
- [[featureflags sub-feature overrides (entity-level flag value overrides)]] - `references` [EXTRACTED]
- [[featureflags sub-feature rules (conditional targeting with rollout percentage)]] - `references` [EXTRACTED]
- [[featureflags.evaluations service — evaluate(), _eval_condition(), _in_rollout(), scope resolution]] - `implements` [EXTRACTED]
- [[featureflags.flags.get (control node)]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine