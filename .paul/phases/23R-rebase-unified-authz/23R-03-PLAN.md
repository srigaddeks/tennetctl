---
phase: 23R-rebase-unified-authz
plan: 03
type: execute
wave: 3
depends_on: [23R-02]
files_modified:
  - frontend/src/app/(dashboard)/iam/roles/page.tsx
  - frontend/src/app/(dashboard)/iam/roles/[roleId]/page.tsx
  - frontend/src/app/(dashboard)/feature-flags/page.tsx
  - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
  - frontend/src/features/iam-roles/capability-grid.tsx
  - frontend/src/features/iam-roles/role-members-tab.tsx
  - frontend/src/features/featureflags/capability-detail.tsx
  - frontend/src/features/featureflags/advanced-rollout-tab.tsx
  - frontend/src/features/iam-roles/hooks/use-role-permissions.ts
  - frontend/src/features/featureflags/hooks/use-capabilities.ts
  - frontend/src/types/api.ts
  - frontend/src/config/features.ts
autonomous: false
---

<objective>
## Goal
Rebase the UI onto the unified model. Roles page becomes a Role Designer with
a single "Capabilities" tab — a flag×action grid grouped by category. Feature
Flags page becomes a Capability Catalog where each flag shows its permissions,
env state, and which roles grant it. The old rules/overrides editor moves
behind an "Advanced rollout" tab shown only when the flag has
`rollout_mode = "targeted"`.

## Purpose
The backend is unified after 23R-02 but the UI still shows two separate tabs
(Permissions + Feature Flags) on roles. This plan makes the interaction match
the mental model the user articulated: one grid, one place to decide what a
role can see and do.

## Output
- Roles page with Capabilities grid + Members tab + (unchanged) Portal Views tab
- Feature Flags page rewritten as Capability Catalog
- Per-flag detail page with Permissions / Granting Roles / Env / Advanced Rollout tabs
- New hooks; old rules/overrides hooks kept but only mounted in Advanced Rollout
- Sidebar relabel: "Feature Flags" → "Capabilities"
</objective>

<context>
## Project Context
@.paul/PROJECT.md
@.paul/STATE.md
@.paul/phases/23R-rebase-unified-authz/CONTEXT.md

## Reference UI patterns
@99_ref/frontend/apps
(explore for role designer + capability catalog UX — read-only)

## Current UI
@frontend/src/app/(dashboard)/iam/roles/page.tsx
@frontend/src/app/(dashboard)/feature-flags/page.tsx
@frontend/src/features/featureflags/flag-rules-panel.tsx
@frontend/src/features/featureflags/flag-overrides-panel.tsx

## Project rules
@.claude/rules/common/core.md
</context>

<acceptance_criteria>

## AC-1: Capability grid
```gherkin
Given I open a role detail page
When the Capabilities tab is selected
Then I see a grid with rows grouped by flag category (Identity, Vault, Audit, Monitoring, Notify, Feature Flags, Platform)
And each row is a flag with N action checkboxes (view, create, update, delete, …)
And currently-granted permissions show checked
And bulk-row selection toggles all actions on a flag
And bulk-column selection toggles one action across all flags in a category
And saving triggers grant/revoke mutations and invalidates role-permissions cache

Given I have unsaved changes
When I navigate away
Then a confirmation modal appears
```

## AC-2: Capability Catalog (Feature Flags page)
```gherkin
Given I open /feature-flags
Then the page title is "Capability Catalog"
And each row shows: flag code, category, scope, access_mode, lifecycle_state, env pills (dev/staging/prod)
And a "Granting roles" count is shown per row
And a "Rollout mode" badge shows 'simple' (default) or 'targeted' (advanced)
And clicking a row opens /feature-flags/{flagId}
```

## AC-3: Flag detail page
```gherkin
Given I open /feature-flags/{flagId}
Then tabs shown: Permissions | Granting Roles | Environments | Advanced Rollout
And Permissions tab lists the (flag × action) rows with inline edit (add/remove action)
And Granting Roles tab lists roles that grant any permission on this flag, grouped by role level
And Environments tab toggles env_dev/env_staging/env_prod and access_mode
And Advanced Rollout tab is only enabled when rollout_mode='targeted'
```

## AC-4: Advanced Rollout tab preserves existing editor
```gherkin
Given a flag with rollout_mode='targeted'
When I open the Advanced Rollout tab
Then the existing condition-tree rule editor (flag-rules-panel) renders
And the existing overrides panel (flag-overrides-panel) renders
And env pills match the current env-picker style (dev=blue, staging=amber, prod=emerald, test=purple)

Given a flag with rollout_mode='simple'
When I toggle rollout_mode to 'targeted'
Then I see a confirmation modal explaining what advanced rollout enables
And on confirm, the Advanced Rollout tab becomes interactive
```

## AC-5: Nav relabel
```gherkin
Given the sidebar
Then the "Feature Flags" entry reads "Capabilities" with sublabel "Catalog & rollout"
And the /feature-flags URL still works (no redirect)
```

## AC-6: Types updated
```gherkin
Given frontend/src/types/api.ts
Then:
  - FeaturePermission { id, flag_code, action_code, flag_name, action_name, description }
  - Role { …, permissions: FeaturePermission[] }  (no scope[])
  - FeatureFlag gains category_code, feature_scope, access_mode, lifecycle_state, rollout_mode
  - old FlagRule / FlagOverride types remain, marked @internal for advanced rollout only
```

## AC-7: Empty & error states
```gherkin
Given a role with zero granted permissions
Then the Capabilities grid shows an empty-state CTA: "This role grants nothing. Pick at least one capability."

Given the backend returns 403 on a grant mutation
Then the specific checkbox reverts
And a toast shows the error message from the response envelope
```

## AC-8: UX verification via Chrome DevTools MCP
```gherkin
- Load /iam/roles, pick a role, grant `vault_secrets.view` + `vault_secrets.create`, save, reload → still granted
- Load /feature-flags, click a flag, verify all 4 tabs render
- Toggle a flag to rollout_mode='targeted', open Advanced Rollout, create a rule, save
- Verify the sidebar shows "Capabilities"
- Verify no console errors / 500s / CORS on any screen
```

</acceptance_criteria>

<execution_notes>

## Component reuse

- `capability-grid.tsx` is new and does 80% of the Role Designer work.
  Render as `<table>` not a flex grid — category headers span full width,
  each flag row has N checkbox cells + a "bulk row" leftmost cell.
- Keep `flag-rules-panel.tsx` and `flag-overrides-panel.tsx` intact —
  they are now the "Advanced Rollout" implementation, not the default.
- Portal Views tab on role page: unchanged from phase 22.

## Performance

- `capability-grid` will render ~15 flags × 8 actions = 120 cells. Fine.
- If it grows past ~50 flags, virtualize with @tanstack/react-virtual later.
  Don't pre-optimize.

## Out of scope

- Changing the SDK evaluation contract (same client code works).
- Drag-and-drop role copy / template import — backlog.
- Per-user permission overrides (use groups).

</execution_notes>

<definition_of_done>
- [ ] Role Designer renders capability grid
- [ ] Capability Catalog renders + flag detail page renders
- [ ] Advanced Rollout tab only interactive when rollout_mode='targeted'
- [ ] All 8 AC walkthroughs pass in chrome-devtools MCP
- [ ] Zero console errors
- [ ] Nav relabeled
- [ ] types/api.ts updated, tsc clean
- [ ] Final polish commit
</definition_of_done>
