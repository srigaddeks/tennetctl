---
milestone: v0.2.0 — Feature Flags + AuthZ Control Plane
phases: 23–27
created: 2026-04-18
status: ready-for-planning
reference: /Users/sri/Documents/tennetctl/99_ref/backend/03_auth_manage/
---

# Milestone Context: v0.2.0 — Feature Flags + AuthZ Control Plane

## Vision

A **unified AuthZ + Feature Control Plane** where roles are the single control
surface: assign a role, get both capabilities (permissions) and feature access
(flags) in one shot. One mental model, one UI to master, one audit trail.

This replaces the fragmented pattern of managing permissions separately from
feature access. Roles become bundles that answer two questions at once:
*what can you do?* and *what can you see?*

## Reference Analysis Summary

Deep analysis of `99_ref/backend/03_auth_manage/` (6,581 lines across 18
sub-features) completed 2026-04-18. Key findings:

### Feature Flag Model (ref: `03_feature_flags/`)

Normalized 4-table schema:

```
fct_flags           — definition (flag_key, scope, default_value, value_type)
fct_flag_states     — per-environment enable/disable + env default
fct_rules           — targeting rules per (flag, environment, priority)
fct_overrides       — force-value per (flag, env, entity_type, entity_id)
```

Dims: `environments`, `value_types` (bool/string/number/json), `scopes`
(global/org/application), `flag_permissions` (view/toggle/write/admin ranked).

**Evaluation priority (first match wins):**
1. Override (entity-specific force value)
2. Rule walk (priority ASC — conditions match AND rollout hash passes)
3. Env default
4. Global default
5. If `is_active=false`, short-circuit to global default

**Targeting rules:** recursive JSON condition tree with operators
`and / or / not / eq / neq / in / startswith / endswith / contains`.
Rollout is deterministic: `hash(flag_key + entity_id) % 100 < rollout_percentage`.

**Audit:** mutations only (create/update/delete of flag or rule). Evaluations
not audited in ref — we should gate this behind a `flags.audit_evaluations`
policy key in our implementation.

### Role + Permission Model (ref: `04_roles/`, `_permission_check.py`)

```
fct_roles                    — code, role_level (platform/org/workspace),
                               scope_org_id, scope_workspace_id, is_system
dim_feature_permissions      — code, feature_flag_code, permission_action_code
                               (e.g. "orgs:manage" namespaced)
lnk_role_feature_permissions — role → permission bundle
lnk_role_flag_permissions    — role → flag + permission_level bundle
```

**Key insight:** permissions are DB-seeded (not code constants), declared in
feature definitions. Roles bundle BOTH permissions AND flag access — exactly
the unified model we want.

**Permission check:** `require_permission(conn, user_id, perm_code, scope_org_id?,
scope_workspace_id?)` called inline (not middleware). 6 UNION ALL branches
resolve perms. **No auto scope inheritance** — workspace check requires both
`scope_org_id` AND `scope_workspace_id` explicitly.

**Assignment path:** User → Group → Role (not direct user → role).

**Caching:** 10-min TTL for role list, 5-min for groups, pattern invalidation
on mutation.

### Access Context (ref: `06_access_context/`)

Per-request resolved bundle: `{user, platform_actions, current_org_actions,
current_workspace_actions}`. Lazy-resolved via FastAPI `Depends()`, cached
5 minutes by `(user_id, org_id, workspace_id)`.

This is the elegant primitive that makes route-level enforcement efficient.

### Portal Views (ref: `16_portal_views/`)

UI-navigation gating: views (`dim_portal_views`) with routes, linked to roles
via `lnk_role_views`. Same 4-path role resolution as access context. Answers
*"what navigation is this user allowed to see?"* at the UI shell level —
distinct from access context which answers *"what actions can they perform?"*.

### Frontend UX Patterns (ref: `99_ref/frontend/apps/web/src/app/(005_admin)/`)

Elegant patterns worth porting verbatim:
1. **Inline edit pickers** — click tag → expand options → select → collapse
2. **Environment status indicator** — highest-reached summary badge
3. **Permission presets** — quick templates (None/View/RW/Full/Admin)
4. **Stat cards with colored left border** — scope/env stats at a glance
5. **Permission matrix** — feature rows × action columns, filterable
6. **Expandable group categories** — category header with stat summary
7. **View/edit toggle in same row** — dual-mode panel
8. **Scope-aware filtering pills** — narrow by org
9. **Smart code auto-generation** — snake_case slug from name
10. **Confirm dialog with semantic color** — info/warning/danger variants

## Unified Core Model (our adaptation)

```
Permission = feature-scoped named capability
             declared in feature.manifest.yaml
             seeded into dim_permissions on boot
             format: "iam:users:write"

Feature Flag = named toggle with typed value + targeting rules
               scoped global/org/application
               evaluated with override → rule-walk → env-default → global-default
               SDK + APISIX compilation for request-path flags

Role = bundle {
  role_level: "platform" | "org" | "workspace"
  scope_org_id: uuid | null
  scope_workspace_id: uuid | null
  permissions[]: permission_code[]
  flag_grants[]: {flag_code, permission_level: view|toggle|write|admin}
  portal_views[]: view_code[]
}

AccessContext = per-request resolved bundle (5-min SWR cache)
                {user_id, org_id, workspace_id,
                 permissions: Set<code>,
                 flags: Map<code, value>,
                 views: Set<code>}
```

## Open Design Questions (resolve during Phase 23-01 planning)

- **Scope inheritance**: ref has NO auto-inheritance (ws check needs both org+ws
  explicitly). Do we keep that (simple, explicit) or add org→workspace
  implicit fall-through (magical, easier callers)?
- **Direct user→role vs user→group→role**: ref uses groups as intermediary.
  Our Phase 6 already has `lnk_user_role` direct assignment. Do we keep direct,
  add optional groups later, or port the group-intermediary pattern?
- **Permission level granularity on flags**: ref uses 4 levels (view/toggle/
  write/admin). Do we need all four? Or simpler (read/write)?
- **Multi-environment**: ref supports dev/staging/prod/test per-flag. We ship
  one environment first, or support env-awareness day one?
- **Evaluation audit**: behind a policy flag? always-on for `write` flags,
  sampled for `view` flags?

## Goals (confirmed by user 2026-04-18)

1. **Full feature flag engine** — targeting rules, % rollout, segment matching,
   SDK evaluation (Python + TS), APISIX gateway compilation.
2. **Feature-scoped permissions** — declared in manifests, seeded to dim, not
   hardcoded. Roles = unified bundle of flag-grants + permissions.
3. **Audit everything** — full trail on mutations; evaluations behind a policy
   flag; access-context resolution traced.
4. **Awesome UX** — port the ref's inline-edit / stat-card / permission-matrix /
   preset / env-status patterns verbatim. Role designer with drag-assign. Live
   evaluation playground. Targeting rule builder.
5. **Skip this milestone:** rate limiting, password hardening, HIBP — those
   belong in v0.1.8 Runtime Hardening (separate track).

## Phase Breakdown

### Phase 23 — Feature Flag Engine Foundation (3 plans)

**Goal:** Working flag engine end-to-end — schema, evaluation, management API,
basic admin UI for verification. No SDK yet, no gateway compilation yet.

- **23-01:** Schema — `09_flags` feature with `fct_flags`, `fct_flag_states`,
  `fct_rules`, `fct_overrides`, `dim_environments`, `dim_value_types`,
  `dim_flag_scopes`. Feature manifest entry. Seeded environments (dev/staging/
  prod). pytest smoke.
- **23-02:** Evaluation engine — rule walker with priority sort, rollout hash,
  JSON condition evaluator (`and/or/not/eq/neq/in/startswith/contains`),
  override precedence, scope resolution. `flags.flag.evaluate` control node
  (tx=caller, read-only). SWR cache per `(flag_key, env, entity)` with
  invalidate-on-mutate. pytest coverage of all 5 evaluation paths.
- **23-03:** Management API + basic admin UI — CRUD for flags/rules/overrides.
  Mutation audit emission. Admin pages at `/admin/flags` with list, create,
  edit (no targeting builder yet — raw JSON for now). Playwright MCP verify.

### Phase 24 — Feature-Scoped Permissions + Role Redesign (3 plans)

**Goal:** Permissions move from hardcoded to manifest-declared. Roles
restructured to carry `role_level + permissions + flag_grants`. `require_permission`
wired site-wide. `AccessContext` primitive live.

- **24-01:** `dim_permissions` schema + feature manifest declaration block +
  boot seeder. Backfill all existing features (iam, audit, vault, notify,
  monitoring) — declare their permissions in manifests. Idempotent upsert on
  manifest reload. pytest: manifest parse + seed + re-seed with changes.
- **24-02:** Role redesign — add `role_level` (platform/org/workspace) +
  `scope_org_id` + `scope_workspace_id` columns. New `lnk_role_flag_grants`
  table (role → flag + permission_level). Migrate existing roles to new shape.
  Role CRUD API updated. pytest + existing role tests green.
- **24-03:** `require_permission(user_id, perm_code, scope_org_id?, scope_ws_id?)`
  helper + `AccessContext` resolver (per-request `Depends()`, 5-min SWR cache
  keyed by `(user_id, org_id, ws_id)`, invalidate on role change). Wire
  `require_permission` into all existing feature routes (iam, audit, vault,
  notify, monitoring). Audit emit on every permission check (behind
  `authz.audit_checks` policy flag; default off for performance).

### Phase 25 — SDK + Gateway Compilation (2 plans)

**Goal:** External consumers can evaluate flags; request-path flags compile
to APISIX; `flags:<perm>` checks exposed to the platform.

- **25-01:** Python + TypeScript SDK thin clients (`tennetctl-sdk-py`,
  `@tennetctl/sdk`). Evaluation endpoint `POST /v1/flags/evaluate` +
  `POST /v1/flags/evaluate-bulk` (batched). Client-side SWR cache of flag
  values (60s TTL). pytest + TS build tests.
- **25-02:** APISIX compilation for request-path flags. When a flag has
  `kind=request` (new flag attribute), sync to APISIX `traffic-split` plugin
  on any flag mutation. APISIX gateway evaluates without hitting backend.
  Audit every APISIX sync operation. pytest + live APISIX integration check.

### Phase 26 — Awesome UX: Flag Dashboard + Role Designer + Playground (3 plans)

**Goal:** Port the reference UX patterns. Three major pages: flag dashboard,
role designer, evaluation playground.

- **26-01:** Flag Dashboard — grouped flag list by category with
  collapse/expand, stat cards with colored left borders, inline environment
  status indicator, inline edit for simple state changes, modal for full
  edit, permission presets on create. `/admin/flags` page.
- **26-02:** Role Designer — permission matrix (feature rows × action columns)
  with search + filter, flag-grants picker with permission-level selection,
  scope-aware filtering pills, expand-to-edit row pattern, duplicate/disable/
  delete actions, audit tab per role. `/admin/roles` page.
- **26-03:** Targeting rule builder + live evaluation playground. Rule builder
  is a form-based tree editor (not freeform JSON — guided add/edit of
  conditions with operator dropdowns + attr/value inputs). Playground:
  input `(flag_code, entity_id, attrs)`, see resolution with source trace
  (which rule matched? what was the hash bucket?). `/admin/flags/playground`.

### Phase 27 — Portal Views + AuthZ Audit Explorer (2 plans)

**Goal:** Role-gated UI navigation + focused audit view for authz events.

- **27-01:** Portal Views — `dim_portal_views` + `lnk_role_views` + resolver
  (4-path, same as ref). Admin UI to define views + assign to roles.
  Frontend navigation shell reads resolved views and renders menu
  accordingly. Portals: `platform`, `iam`, `audit`, `monitoring`, `notify`,
  `vault`, `flags`.
- **27-02:** AuthZ Audit Explorer — pre-filtered view of audit events with
  categories `authz.permission.checked`, `flags.evaluated`,
  `authz.access_context.resolved`, `roles.*`, `flags.*.mutated`. Timeline
  chart + per-permission aggregates + per-flag-evaluation aggregates.
  Saved views for common admin queries. `/audit/authz` page.

## Phase Summary

| Phase | Theme | Plans | Estimated |
|-------|-------|-------|-----------|
| 23 | Feature Flag Engine Foundation | 3 | ~3 sessions |
| 24 | Permissions + Role Redesign | 3 | ~3 sessions |
| 25 | SDK + Gateway | 2 | ~2 sessions |
| 26 | Awesome UX | 3 | ~3 sessions |
| 27 | Portal Views + AuthZ Audit | 2 | ~2 sessions |
| **Total** | **v0.2.0** | **13 plans** | **~13 sessions** |

## Depends On

- Phase 6 (Roles/Groups backend) — existing role tables, extend schema
- Phase 9 (Feature Flags stub) — repurpose schema ids if any
- Phase 10 (Audit analytics) — `audit.events.emit` used throughout,
  audit explorer pattern reused in Phase 27
- Phase 20 (AuthPolicy) — `flags.audit_evaluations`, `authz.audit_checks`
  policy flags
- Phase 22 (IAM Enterprise) — complete; provides org/workspace scope context
- Vault — flag targeting rules may reference vault keys
- APISIX — Phase 25-02 requires APISIX running (already in docker-compose)

## Tech Stack Additions

- **Python:** no new deps (JSON eval inline, hashlib for rollout)
- **TypeScript SDK:** zero-dep (native fetch), published as
  `@tennetctl/sdk`
- **Python SDK:** `httpx` only (already in requirements)
- **Frontend:** no new deps (already have Tailwind + TanStack)

## Non-Goals for v0.2.0

- Visual drag-drop rule builder (form-based is fine)
- A/B testing / experiments (flags are boolean + variant; not experiments)
- Automatic permission discovery via AST (manifest declaration is explicit)
- User-level flag overrides UI (admin API supports; UI deferred)
- Flag history / versioning beyond audit trail (no separate version table)
- Migration path from Unleash/LaunchDarkly (greenfield; deferred to v0.2.1)
