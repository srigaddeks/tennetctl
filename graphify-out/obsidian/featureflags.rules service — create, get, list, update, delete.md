---
source_file: "backend/02_features/09_featureflags/sub_features/03_rules/service.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.rules service — create, get, list, update, delete

## Connections
- [[featureflags.flags.get (control node)]] - `calls` [EXTRACTED]
- [[featureflags.rules repository — 20_fct_rules, v_rules, list_rules_for_eval fast-path]] - `calls` [EXTRACTED]
- [[featureflags.rules routes — v1flag-rules (GET, POST, PATCH, DELETE)]] - `calls` [EXTRACTED]
- [[featureflags.rules.create (effect node)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine