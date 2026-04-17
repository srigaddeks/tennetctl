---
source_file: "backend/02_features/09_featureflags/sub_features/05_evaluations/service.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.evaluations service — evaluate(), _eval_condition(), _in_rollout(), scope resolution

## Connections
- [[Condition tree evaluator — recursive eval supporting andornoteqingtcontainsexistsrollout]] - `implements` [EXTRACTED]
- [[Deterministic rollout bucketing — sha256(flag_keyentity_id) mod 100  percentage]] - `implements` [EXTRACTED]
- [[Flag evaluation pipeline scope resolution → overrides → rules → env default → flag default]] - `implements` [EXTRACTED]
- [[featureflags.evaluations routes — POST v1evaluate]] - `calls` [EXTRACTED]
- [[featureflags.evaluations.resolve (control node)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine