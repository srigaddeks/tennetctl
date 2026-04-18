---
phase: 23R-rebase-unified-authz
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - 03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/02_in_progress/20260418_050_rebase-flags-as-capabilities.sql
  - 03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/seeds/01_dim_permission_actions.yaml
  - 03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/seeds/02_dim_feature_flag_categories.yaml
  - 03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/seeds/03_dim_feature_flags.yaml
  - 03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/seeds/04_dim_feature_permissions.yaml
autonomous: false
---

<objective>
## Goal
Land the unified flag+permission schema. Rename/extend `dim_feature_flags` to
carry category/scope/access_mode/lifecycle/env toggles. Add `dim_permission_actions`
and `dim_feature_permissions`. Replace `lnk_role_scopes` + `lnk_role_flags` with a
single `lnk_role_feature_permissions`. Seed actions, categories, one flag per
existing sub-feature, and their `(flag × action)` permissions. Data-migrate
existing role grants.

## Purpose
This is the schema substrate for phase 23R. Everything in 23R-02 (resolver) and
23R-03 (UI) depends on this landing cleanly. Keep it a single migration with a
complete DOWN so we can roll back if the resolver rewrite finds a blocker.

## Output
- 1 migration file with UP + DOWN
- 4 seed YAMLs (actions, categories, flags, feature_permissions)
- Data-migration block inside the UP that rewrites existing role grants
</objective>

<context>
## Project Context
@.paul/PROJECT.md
@.paul/STATE.md
@.paul/phases/23R-rebase-unified-authz/CONTEXT.md

## Reference (read before writing schema)
@99_ref/backend/03_auth_manage/03_feature_flags/models.py
@99_ref/backend/03_auth_manage/03_feature_flags/schemas.py
@99_ref/backend/03_auth_manage/04_roles/models.py

## Current schema (read before writing migration)
@03_docs/features/09_featureflags/05_sub_features/00_bootstrap/09_sql_migrations/01_migrated/
@03_docs/features/03_iam/05_sub_features/04_roles/09_sql_migrations/

## Project rules
@.claude/rules/common/database.md
</context>

<acceptance_criteria>

## AC-1: New dim tables seeded
```gherkin
Given a fresh migration run
When I query `SELECT count(*) FROM "09_featureflags"."01_dim_permission_actions"`
Then the count is 8
And the codes are: view, create, update, delete, assign, configure, export, impersonate

When I query `SELECT count(*) FROM "09_featureflags"."02_dim_feature_flag_categories"`
Then the count is >= 8 (iam, vault, monitoring, audit, notify, featureflags, platform, nodes)

When I query `SELECT count(*) FROM "09_featureflags"."03_dim_feature_flags"`
Then every existing sub-feature has exactly one flag row
And each row has category_code, feature_scope, access_mode, lifecycle_state,
    env_dev/env_staging/env_prod columns populated

When I query `SELECT count(*) FROM "09_featureflags"."04_dim_feature_permissions"`
Then every flag has at least one permission (`.view` at minimum)
And common capabilities have full CRUD (view/create/update/delete)
```

## AC-2: Old tables dropped (no data migration)
```gherkin
Given v0.2.0 is pre-release and we accept a clean cut
When the migration completes
Then `dim_scopes`, `lnk_role_scopes`, `lnk_role_flags` no longer exist
And `v_role_scopes` no longer exists
And the DOWN migration recreates them empty (structure only)
```

## AC-3: Roles reseed against the new catalog
```gherkin
Given fresh seed runs
Then the 7 system roles (platform_super_admin, org_admin, org_member,
  org_viewer, workspace_admin, workspace_contributor, workspace_viewer)
  exist with sensible default grants on the new feature_permissions
And platform_super_admin grants every permission on every flag
And org_viewer grants only '.view' actions on org-scoped flags
```

## AC-4: Indexes + constraints
```gherkin
- PK on each table using snake_case `pk_*` names
- FK from lnk_role_feature_permissions.role_id → fct_roles.id with ON DELETE CASCADE
- FK from lnk_role_feature_permissions.feature_permission_id → dim_feature_permissions.id
- UNIQUE(role_id, feature_permission_id) partial index where deleted_at IS NULL
- UNIQUE(flag_id, action_id) on dim_feature_permissions (one perm per flag × action)
- CHK on dim_feature_flags.access_mode IN ('public','authenticated','permissioned')
- CHK on dim_feature_flags.lifecycle_state IN ('planned','active','deprecated','retired')
- CHK on dim_feature_flags.feature_scope IN ('platform','org','workspace','product')
- CHK on dim_feature_flags.rollout_mode IN ('simple','targeted')  -- default 'simple'
- COMMENT ON every table + every column
```

## AC-5: Views updated
```gherkin
- Create v_feature_permissions resolving flag + action codes
- Create v_role_permissions resolving role.code, flag.code, action.code in one join
- Drop v_role_scopes (no longer exists)
- Ensure drop order respects dependencies
```

## AC-6: DOWN works
```gherkin
Given the UP has applied
When I run the DOWN migration
Then dim_scopes, lnk_role_scopes, lnk_role_flags are restored with their data
And the new tables are dropped
And views are rebuilt to their pre-migration shape
```

## AC-7: Seed idempotency
```gherkin
When I re-run the seeder
Then it is a no-op (ON CONFLICT DO NOTHING on all seed inserts)
And no rows are duplicated
```

</acceptance_criteria>

<execution_notes>

## Key design decisions

1. **Put the capability catalog in `09_featureflags` schema, not `03_iam`.**
   The flags were already there. Roles and the link table move in too — this
   is the single source of truth for "what capabilities exist and who grants
   them." The role ID still lives in `03_iam` (`fct_roles`) but the grant
   table lives here since its rows are keyed by flag permissions.

2. **Keep flag codes stable.** Existing flag codes (`new_checkout_flow`, etc.)
   become capability codes. Seed adds new capability-style flags
   (`orgs`, `vault_secrets`, …) in addition.

3. **`rollout_mode` column** is the opt-in for the advanced rollout engine.
   Default `'simple'` — resolver does env + access_mode + role grant.
   `'targeted'` — falls through to the existing rules/overrides path.

4. **Drop `dim_scopes` in the same migration, not a follow-up.** No point
   leaving a broken table around. If we need to roll back, the DOWN restores
   it.

## Out of scope for this plan

- Touching `authz.py` / `require_permission` — that is 23R-02.
- UI changes — that is 23R-03.
- Updating existing route handlers to use new permission codes — 23R-02.

</execution_notes>

<definition_of_done>
- [ ] Migration applies cleanly on a fresh DB
- [ ] Migration applies cleanly on a DB with existing role grants
- [ ] DOWN fully reverts
- [ ] Seed files idempotent
- [ ] All 4 dim tables populated
- [ ] Data-migration preserves grants (tested with a scripted before/after diff)
- [ ] Views rebuilt
- [ ] `graphify update .` runs clean
</definition_of_done>
