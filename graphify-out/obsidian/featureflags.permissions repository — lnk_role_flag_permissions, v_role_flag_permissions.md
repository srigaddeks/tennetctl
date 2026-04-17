---
source_file: "backend/02_features/09_featureflags/sub_features/02_permissions/repository.py"
type: "code"
community: "Feature Flag Evaluation Engine"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Feature_Flag_Evaluation_Engine
---

# featureflags.permissions repository — lnk_role_flag_permissions, v_role_flag_permissions

## Connections
- [[DB table 09_featureflags.04_dim_flag_permissions (view, toggle, write, admin)]] - `references` [EXTRACTED]
- [[DB table 09_featureflags.40_lnk_role_flag_permissions]] - `references` [EXTRACTED]
- [[DB view 09_featureflags.v_role_flag_permissions]] - `references` [EXTRACTED]
- [[IAM cross-reference 03_iam.42_lnk_user_roles (used by permission checks)]] - `references` [EXTRACTED]
- [[IAM cross-reference 03_iam.44_lnk_role_scopes + 03_dim_scopes (flagsadminall scope)]] - `references` [EXTRACTED]
- [[featureflags.permissions service — grant, revoke, check_flag_permission, list]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Feature_Flag_Evaluation_Engine