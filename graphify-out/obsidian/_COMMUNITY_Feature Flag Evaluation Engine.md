---
type: community
cohesion: 0.06
members: 41
---

# Feature Flag Evaluation Engine

**Cohesion:** 0.06 - loosely connected
**Members:** 41 nodes

## Members
- [[Condition tree evaluator — recursive eval supporting andornoteqingtcontainsexistsrollout]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[DB table 09_featureflags.01_dim_environments (dev, staging, prod, test)]] - code - backend/02_features/09_featureflags/sub_features/03_rules/repository.py
- [[DB table 09_featureflags.04_dim_flag_permissions (view, toggle, write, admin)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[DB table 09_featureflags.20_fct_rules]] - code - backend/02_features/09_featureflags/sub_features/03_rules/repository.py
- [[DB table 09_featureflags.21_fct_overrides]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/repository.py
- [[DB table 09_featureflags.40_lnk_role_flag_permissions]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[DB view 09_featureflags.v_overrides]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/repository.py
- [[DB view 09_featureflags.v_role_flag_permissions]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[DB view 09_featureflags.v_rules]] - code - backend/02_features/09_featureflags/sub_features/03_rules/repository.py
- [[Deterministic rollout bucketing — sha256(flag_keyentity_id) mod 100  percentage]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[Flag evaluation pipeline scope resolution → overrides → rules → env default → flag default]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[IAM cross-reference 03_iam.01_dim_entity_types (used by overrides entity_type resolution)]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/repository.py
- [[IAM cross-reference 03_iam.42_lnk_user_roles (used by permission checks)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[IAM cross-reference 03_iam.44_lnk_role_scopes + 03_dim_scopes (flagsadminall scope)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[Permission rank system — view=1, toggle=2, write=3, admin=4]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/service.py
- [[check_flag_permission — shared guard used by overrides, rules, evaluations]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/service.py
- [[featureflags sub-feature evaluations (flag resolution engine)]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[featureflags sub-feature overrides (entity-level flag value overrides)]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/service.py
- [[featureflags sub-feature permissions (grantrevokelist)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/service.py
- [[featureflags sub-feature rules (conditional targeting with rollout percentage)]] - code - backend/02_features/09_featureflags/sub_features/03_rules/service.py
- [[featureflags.evaluations routes — POST v1evaluate]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/routes.py
- [[featureflags.evaluations schemas — EvaluateRequest, EvaluateResponse, EvalContext, EvalReason]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/schemas.py
- [[featureflags.evaluations service — evaluate(), _eval_condition(), _in_rollout(), scope resolution]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[featureflags.evaluations.resolve (control node)]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[featureflags.flags.get (control node)]] - code - backend/02_features/09_featureflags/sub_features/01_flags/nodes/featureflags_flags_get.py
- [[featureflags.overrides repository — 21_fct_overrides, v_overrides, list_overrides_for_eval fast-path]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/repository.py
- [[featureflags.overrides routes — v1flag-overrides (GET, POST, PATCH, DELETE)]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/routes.py
- [[featureflags.overrides schemas — OverrideCreate, OverrideUpdate, OverrideRead]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/schemas.py
- [[featureflags.overrides service — create, get, list, update, delete]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/service.py
- [[featureflags.overrides.set (effect node)]] - code - backend/02_features/09_featureflags/sub_features/04_overrides/nodes/featureflags_overrides_set.py
- [[featureflags.permissions repository — lnk_role_flag_permissions, v_role_flag_permissions]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/repository.py
- [[featureflags.permissions routes — v1flag-permissions (GET, POST, DELETE)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/routes.py
- [[featureflags.permissions schemas — RoleFlagPermissionCreate, RoleFlagPermissionRead]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/schemas.py
- [[featureflags.permissions service — grant, revoke, check_flag_permission, list]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/service.py
- [[featureflags.permissions.grant (effect node)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/nodes/featureflags_permissions_grant.py
- [[featureflags.permissions.revoke (effect node)]] - code - backend/02_features/09_featureflags/sub_features/02_permissions/nodes/featureflags_permissions_revoke.py
- [[featureflags.rules repository — 20_fct_rules, v_rules, list_rules_for_eval fast-path]] - code - backend/02_features/09_featureflags/sub_features/03_rules/repository.py
- [[featureflags.rules routes — v1flag-rules (GET, POST, PATCH, DELETE)]] - code - backend/02_features/09_featureflags/sub_features/03_rules/routes.py
- [[featureflags.rules schemas — RuleCreate, RuleUpdate, RuleRead]] - code - backend/02_features/09_featureflags/sub_features/03_rules/schemas.py
- [[featureflags.rules service — create, get, list, update, delete]] - code - backend/02_features/09_featureflags/sub_features/03_rules/service.py
- [[featureflags.rules.create (effect node)]] - code - backend/02_features/09_featureflags/sub_features/03_rules/nodes/featureflags_rules_create.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Feature_Flag_Evaluation_Engine
SORT file.name ASC
```
