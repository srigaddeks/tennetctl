# Phase 37 UX Audit — SUMMARY

**Phase:** 37-ux-audit
**Status:** ✅ Complete (Batch 1 — audit + high-priority fixes)
**Date:** 2026-04-18

## What shipped

### Audit
- `AUDIT.md` — four parallel exploration agents surveyed 60+ files and produced a prioritized fix list across IAM, Account, Vault, Audit, Notify, Monitoring, Feature Flags, Catalog, System, and shared primitives

### Shared primitive additions
- **`Breadcrumb` component** at `frontend/src/components/breadcrumb.tsx` — aria-compliant nav with `›` separators
- **PageHeader enhanced** — optional `breadcrumbs` prop wires the new component above the title
- **`ConfirmDialog` component** at `frontend/src/components/confirm-dialog.tsx` — standardized Modal-based confirmation (replaces `window.confirm()`)
- **`Checkbox` primitive** added to `ui.tsx` — `<Checkbox label="..." hint="...">` with consistent styling + dark mode
- **Toast `warning` tone** — amber-themed, with `!` glyph

### Session + data layer
- **401 handling** in `lib/api.ts` — on `401` response, redirects to `/auth/signin?next=<current path>`; exempts auth routes + `/setup`

### IAM Users workflow
- List page: drawer replaced with `router.push('/iam/users/{id}')`; search by email/display_name; account-type labels instead of raw codes (`email_password` → `Email + Password`); row testids; count badge
- Detail page: breadcrumbs `Identity › Users › <user>` wired in

### IAM Workspaces workflow
- Detail page: breadcrumbs `Identity › Workspaces › <slug>`

### IAM Portal Views N+1 fix
- **Before:** `ViewCardWithCount` called `useRoleViews(role.id)` inside `roles.map()` (React hook rules violation); `RoleCheckRow` re-fetched per row (duplicate with parent `useRoleViews(undefined)`)
- **After:** single `useRoleViews(undefined)` fetches all assignments; `grantsByView` Map computed once via `useMemo`; `RoleCheckRow` uses the `granted` prop already passed from parent — no duplicate fetches

### 7 IAM Security pages rewritten
Every page previously used custom headings + inline `fetch()` calls. Now all seven use `PageHeader` + `apiFetch` + TanStack Query hooks + standard UI primitives, matching the rest of the portal.

| Page | Before (lines) | After (lines) |
|---|---|---|
| `/iam/security/sso` | 229 | 361 |
| `/iam/security/saml` | 186 | 307 |
| `/iam/security/scim` | 140 | 293 |
| `/iam/security/mfa` | 73 | 119 |
| `/iam/security/ip-allowlist` | 102 | 259 |
| `/iam/security/siem` | 123 | 301 |
| `/iam/security/tos` | 104 | 320 |

Seven new hook modules under `frontend/src/features/iam-security/hooks/`:
`use-sso.ts`, `use-saml.ts`, `use-scim.ts`, `use-mfa.ts`, `use-ip-allowlist.ts`, `use-siem.ts`, `use-tos.ts`

All rewrites:
- Add breadcrumbs `Identity › Security › <page>`
- Replace `window.confirm()` with Modal confirmations
- Use `EmptyState` / `ErrorState` / `Skeleton` consistently
- Add testids
- Remove hardcoded `bg-gray-50` etc.; use zinc + dark: variants

## Verification
- `npx tsc --noEmit` — clean
- `npx next build` — success; all routes present

## Deferred to Batch 2 (polish, out of scope this round)
- Mobile sidebar collapse (requires drawer component)
- CSV export on tables
- Command palette ⌘K
- Table sort indicators + pagination component
- Notify Deliveries retry UX + detail page
- Notify template preview sanitization (DOMPurify)
- Audit live tail filter respect
- Feature Flag evaluator full rule tree
- Monitoring trace pagination
- System Health "copy diagnostic bundle" button
- Confirm-dialog rollout to remaining pages (memberships, dashboards, rules, silences, saved-queries, suppressions)
- Status-field unification on user detail (currently dual; `is_active` vs `status`)

## Decisions
- Kept OrgScopedResourcePage untouched (groups + applications are healthy, not 🟡)
- Kept Workspaces list drawer removal (already done 35-01)
- Security pages: preserved existing backend endpoints + behavior; no backend changes
- SIEM UI shows all `kind` options but warns only `webhook` is wired (matches existing behavior)
