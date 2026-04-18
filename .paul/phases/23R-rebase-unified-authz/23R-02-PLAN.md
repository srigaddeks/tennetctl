---
phase: 23R-rebase-unified-authz
plan: 02
type: execute
wave: 2
depends_on: [23R-01]
files_modified:
  - backend/01_core/authz.py
  - backend/02_features/03_iam/sub_features/04_roles/service.py
  - backend/02_features/03_iam/sub_features/04_roles/repository.py
  - backend/02_features/03_iam/sub_features/04_roles/routes.py
  - backend/02_features/03_iam/sub_features/04_roles/schemas.py
  - backend/02_features/09_featureflags/service.py
  # Only 2 files actually import require_permission today (grep confirmed):
  #   - backend/01_core/authz.py (being rewritten)
  #   - backend/01_core/middleware.py (AccessContext caller)
  # Route files use _require_user/_require_org (session extractors), not
  # require_permission directly. A call-site migration script is therefore
  # NOT needed.
  - backend/01_core/middleware.py  # AccessContext resolution
  - tests/test_authz_resolver.py
  - tests/test_role_permission_grants.py
autonomous: false
---

<objective>
## Goal
Replace the current `require_permission(scope_code)` with the ref-style
6-branch UNION resolver that checks `(flag_code, action_code)` grants. Update
every route handler across the backend to use the new permission codes. Wire
AccessContext to pre-resolve the caller's full permission set for the request.

## Purpose
Make the schema from 23R-01 actually gate access. Until this ships, the new
tables are dead weight and the old scope-based checks still run.

## Output
- New `backend/01_core/authz.py` implementing `require_permission(conn, user_id, "flag.action", scope_org_id=..., scope_workspace_id=...)`
- All call sites migrated (~60 routes across iam/vault/audit/monitoring/notify/featureflags)
- Updated `AccessContext` with pre-resolved permission list + 5-min SWR cache
- Pytest coverage of all 6 branches + the scope-filtering logic
</objective>

<context>
## Project Context
@.paul/PROJECT.md
@.paul/STATE.md
@.paul/phases/23R-rebase-unified-authz/CONTEXT.md

## Reference (port this, adapted)
@99_ref/backend/03_auth_manage/_permission_check.py
@99_ref/backend/03_auth_manage/06_access_context/

## Current state (the thing being replaced)
@backend/01_core/authz.py
@backend/01_core/middleware.py
@backend/02_features/03_iam/sub_features/04_roles/service.py

## Project rules
@.claude/rules/python.md
@.claude/rules/common/core.md
</context>

<acceptance_criteria>

## AC-1: Resolver — single-path join
```gherkin
Given a user with a direct global role grant (lnk_user_roles.org_id IS NULL)
When require_permission(conn, user, "vault_secrets.view") runs
Then the join succeeds and no AppError("FORBIDDEN") raised

Given a user with an org-scoped role grant (lnk_user_roles.org_id = ORG_A)
When require_permission(conn, user, "orgs.update", scope_org_id=ORG_A)
Then the join succeeds for ORG_A, raises FORBIDDEN for ORG_B

Given a user with an expired grant (ur.expires_at < NOW())
Then the join rejects and FORBIDDEN is raised

Given a user with a revoked grant (ur.revoked_at IS NOT NULL)
Then the join rejects and FORBIDDEN is raised

Given a user with no grants anywhere
When require_permission runs
Then AppError("FORBIDDEN", "Permission required: flag.action", 403) raised
```

## AC-2: All call sites migrated
```gherkin
Given the old scope codes (e.g., 'iam.orgs.view')
When I grep the backend
Then zero call sites still pass old-style scope codes to require_permission
And every call uses the new flag.action format (e.g., 'orgs.view')
```

## AC-3: AccessContext pre-resolves full permission set
```gherkin
Given a request comes in with a valid session
When middleware runs
Then AccessContext.permissions contains a frozenset of "flag.action" strings
  the caller holds at the request's (org, workspace) scope
And subsequent require_permission calls can check the frozenset first
  (in-process fast path) before falling back to the DB resolver
And the cache is per (user_id, org_id, workspace_id) with 5-min SWR TTL
And cache invalidates on role/grant change via invalidate_access_cache()
```

## AC-4: API key scopes
```gherkin
Given a request made with an API key that has limited scopes
When require_permission is called with a permission not in the API key scopes
Then AuthorizationError raised before even hitting the DB
And the error message names the missing permission
```

## AC-5: Audit on grant/revoke
```gherkin
Given an admin grants a feature_permission to a role
Then event `iam.role.permission_granted` is emitted with
  properties.flag_code + properties.action_code + properties.role_code

Given an admin revokes a feature_permission from a role
Then event `iam.role.permission_revoked` is emitted with the same fields

Given a permission check fails
Then event `iam.authz.denied` is emitted at category=access, outcome=failure
  with properties.permission_code + properties.scope_org_id + properties.scope_workspace_id
```

## AC-6: Roles API uses feature_permissions
```gherkin
When GET /v1/iam/roles/{role_id}
Then response.data.permissions is a list of objects with
  { id, feature_permission_id, flag_code, action_code, name, description }
And no `scope_code` field remains on the response
```

## AC-7: Tests cover all 6 branches
```gherkin
- test_global_role_grants_permission
- test_org_scoped_role_matches_only_its_org
- test_expired_role_denies
- test_revoked_role_denies
- test_deprecated_flag_denies
- test_no_grants_raises_forbidden
- test_api_key_scope_enforcement
- test_access_context_cache_invalidation_on_role_update
- test_access_context_per_org_scope_isolation
```

</acceptance_criteria>

<execution_notes>

## Adaptation notes vs ref

- Ref has 6 branches including GRC role assignments (branches 5 + 6).
  **Drop them entirely** — no TODO, no commented block, no extension point.
  TennetCTL is a generic control plane; GRC is one domain someone could build
  on top, not something baked into the authz core.

- Ref uses `_ORG_CASE` and `_WS_CASE` string-built CASE statements for the
  membership_type → role code mapping. Port verbatim, but pull the
  membership_type → role code map from `dim_org_membership_types` and
  `dim_workspace_membership_types` at import time (not hardcoded).

- Ref uses `utc_now_sql()` and `scope_org_id::UUID`. In tennetctl our
  UUIDs are stored as VARCHAR(36). Drop the `::UUID` casts.

## AccessContext caching

- Key: `access:{user_id}:{org_id or '_'}:{workspace_id or '_'}`
- Value: frozenset of "flag.action" strings + resolved_at timestamp
- TTL: 300s with SWR — serve stale while revalidating in a background task
- Invalidation hooks to call `invalidate_access_cache(user_id)`:
  - role.permission_granted / revoked
  - role created / deleted
  - group membership added / removed
  - user's org membership changed

## Route migration pattern

For each route handler that currently does:
```python
await require_permission(conn, user_id, "iam.orgs.update")
```

Replace with:
```python
await require_permission(conn, user_id, "orgs.update", scope_org_id=org_id)
```

The scope_org_id comes from the path param or request context — this is a
meaningful change (scope was implicit before; now it's explicit).

## Call-site migration script

Write a one-off script in `scripts/migrate_permission_codes.py` that:
1. Parses every route file
2. Finds require_permission calls
3. Rewrites the code string using the mapping from 23R-01
4. Adds scope_org_id / scope_workspace_id kwargs from path params

Run it, review the diff, commit. Don't hand-edit 60 files.

</execution_notes>

<definition_of_done>
- [ ] `authz.py` implements 4-branch UNION (2 dropped for no-GRC)
- [ ] All route handlers migrated via the script + reviewed diff
- [ ] AccessContext returns frozenset of "flag.action" codes
- [ ] 11+ pytest tests passing
- [ ] `require_permission` grep returns zero old-style scope codes
- [ ] No CORS / 500 regressions on backend restart
- [ ] Audit events emit with new properties
</definition_of_done>
