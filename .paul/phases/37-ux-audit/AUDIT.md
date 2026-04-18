# TennetCTL UX Audit — v0.2.4 professional-polish pass

**Date:** 2026-04-18
**Scope:** Every shipped admin page + shared primitives
**Method:** Four parallel exploration agents surveyed 60+ files

## Prioritized fix list (by impact × effort)

### 🔴 CRITICAL — ship in this batch

| # | Issue | Files | Effort |
|---|---|---|---|
| 1 | 7 IAM security pages (sso/saml/scim/mfa/ip-allowlist/siem/tos) use custom headers + inline fetch — inconsistent with rest of app | `frontend/src/app/(dashboard)/iam/security/{sso,saml,scim,mfa,ip-allowlist,siem,tos}/page.tsx` | High (rewrite each to use PageHeader + standard UI) |
| 2 | Users list → detail page orphaned; list uses drawer instead of navigating | `frontend/src/app/(dashboard)/iam/users/page.tsx` | Low |
| 3 | Portal Views N+1 query: `useRoleViews(role.id)` per role | `frontend/src/app/(dashboard)/iam/security/portal-views/page.tsx` | Medium |
| 4 | Status field mismatch: `/iam/users/[id]` sends `status:"active"` but drawer sends `is_active:boolean` | `frontend/src/app/(dashboard)/iam/users/[id]/page.tsx` | Low |
| 5 | No 401 redirect: session expiry → dead page | `frontend/src/lib/api.ts` | Low |

### 🟡 HIGH — also ship

| # | Issue | Effort |
|---|---|---|
| 6 | Breadcrumb component + PageHeader integration | Low |
| 7 | Warning tone for Toast (amber) | Low |
| 8 | Checkbox primitive extracted | Low |
| 9 | Confirm modal primitive (replace `window.confirm()` gradually) | Medium |
| 10 | Status-code mismatch: users drawer uses `is_active`, detail uses `status` — unify | Low |
| 11 | Copy-link button for detail pages | Low |

### 🟢 POLISH — next round (deferred this batch)

- Mobile sidebar collapse (requires drawer component)
- CSV export on tables
- Command palette ⌘K
- Table sort indicators + pagination component
- Feature Flag evaluator full rule tree
- Notify Deliveries retry UX + detail page
- Notify template preview sanitization (DOMPurify)
- Audit live tail filter respect
- Notify settings split into tabs
- Monitoring dashboard DSL editor syntax highlighting
- Monitoring trace pagination
- Alert acknowledge/resolve
- Alert rule pause duration dropdown
- System health "copy diagnostic" button

## Execution plan

**Batch A — Primitives** (small, high-leverage):
- Add warning tone to Toast
- Add Checkbox primitive
- Add Breadcrumb component
- Add ConfirmDialog primitive
- Add 401 redirect to apiFetch

**Batch B — Users list → detail link + is_active unification**

**Batch C — IAM security pages standardization** (the big one)

**Batch D — Portal Views N+1 + Copy-link button**

Each batch: typecheck + build after, commit before moving on.
