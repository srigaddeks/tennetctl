---
source_file: "backend/02_features/09_featureflags/sub_features/04_overrides/repository.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.overrides repository — 21_fct_overrides, v_overrides, list_overrides_for_eval fast-path

## Connections
- [[DB table 09_featureflags.01_dim_environments (dev, staging, prod, test)]] - `shares_data_with` [EXTRACTED]
- [[DB table 09_featureflags.21_fct_overrides]] - `references` [EXTRACTED]
- [[DB view 09_featureflags.v_overrides]] - `references` [EXTRACTED]
- [[IAM cross-reference 03_iam.01_dim_entity_types (used by overrides entity_type resolution)]] - `references` [EXTRACTED]
- [[featureflags.overrides service — create, get, list, update, delete]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine