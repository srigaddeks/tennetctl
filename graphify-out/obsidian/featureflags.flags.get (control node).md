---
source_file: "backend/02_features/09_featureflags/sub_features/01_flags/nodes/featureflags_flags_get.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.flags.get (control node)

## Connections
- [[Flag evaluation pipeline scope resolution → overrides → rules → env default → flag default]] - `references` [INFERRED]
- [[featureflags sub-feature overrides (entity-level flag value overrides)]] - `conceptually_related_to` [INFERRED]
- [[featureflags sub-feature permissions (grantrevokelist)]] - `conceptually_related_to` [INFERRED]
- [[featureflags sub-feature rules (conditional targeting with rollout percentage)]] - `conceptually_related_to` [INFERRED]
- [[featureflags.overrides service — create, get, list, update, delete]] - `calls` [EXTRACTED]
- [[featureflags.permissions service — grant, revoke, check_flag_permission, list]] - `calls` [EXTRACTED]
- [[featureflags.rules service — create, get, list, update, delete]] - `calls` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Feature_Flag_Evaluation_Engine