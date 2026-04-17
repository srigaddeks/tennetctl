---
source_file: "backend/02_features/09_featureflags/sub_features/02_permissions/service.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.permissions service — grant, revoke, check_flag_permission, list

## Connections
- [[Permission rank system — view=1, toggle=2, write=3, admin=4]] - `implements` [EXTRACTED]
- [[check_flag_permission — shared guard used by overrides, rules, evaluations]] - `implements` [EXTRACTED]
- [[featureflags.flags.get (control node)]] - `calls` [EXTRACTED]
- [[featureflags.permissions repository — lnk_role_flag_permissions, v_role_flag_permissions]] - `calls` [EXTRACTED]
- [[featureflags.permissions routes — v1flag-permissions (GET, POST, DELETE)]] - `calls` [EXTRACTED]
- [[featureflags.permissions.grant (effect node)]] - `calls` [EXTRACTED]
- [[featureflags.permissions.revoke (effect node)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine