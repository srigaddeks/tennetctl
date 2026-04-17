---
source_file: "backend/02_features/09_featureflags/sub_features/03_rules/repository.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.rules repository — 20_fct_rules, v_rules, list_rules_for_eval fast-path

## Connections
- [[DB table 09_featureflags.01_dim_environments (dev, staging, prod, test)]] - `shares_data_with` [EXTRACTED]
- [[DB table 09_featureflags.20_fct_rules]] - `references` [EXTRACTED]
- [[DB view 09_featureflags.v_rules]] - `references` [EXTRACTED]
- [[featureflags.rules service — create, get, list, update, delete]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine