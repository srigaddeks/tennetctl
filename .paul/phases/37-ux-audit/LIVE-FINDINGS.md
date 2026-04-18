# Live Browser Walkthrough — Findings + Fixes

**Date:** 2026-04-18
**Method:** Chrome DevTools MCP, headful browser, real backend (Postgres + backend + next dev, all up).
**Auth:** signed in as `demo.admin@local.test` against live IAM backend.
**Screenshots:** 30+ captured under `.paul/phases/37-ux-audit/screenshots/`

## Features walked

| Area | Pages visited | Quality bar |
|---|---|---|
| **Overview** | `/` | ✅ clean feature grid |
| **IAM Directory** | orgs, workspaces, users, memberships, roles | ✅ Roles best-in-class, users 🟡 below |
| **IAM Security** | policy, sso, saml (plus scim/mfa/ip/siem/tos rewritten in Batch 1) | ✅ standardized |
| **Vault** | secrets, configs | ✅ clean lists |
| **Audit** | explorer, authz | ✅ PRO: filters + stats + CSV + live tail |
| **Feature Flags** | list, detail | ✅ PRO: pills, stats, grouped, inline toggle |
| **Monitoring** | overview, logs, metrics, traces | ✅ explorer is tight |
| **Catalog** | features + sub-features | 🟡 dense, no search |
| **Notify** | templates, settings | ✅ list + groupings |
| **System Health** | health | 🔴 count discrepancy (fixed) |
| **Account** | sessions, api-keys, privacy | not this pass |

## Real gaps observed + fixed in this batch

### 🔴 Critical

1. **System Health "Modules 7/6 enabled"** — `core` was in the enabled list but absent from `MODULE_ROUTERS`, making the count look broken. **Fix:** backend `/health` now unions `MODULE_ROUTERS.keys()` with an `always_on = {"core"}` set so enabled and available both report 7. Visible in UI: "7/7 enabled", core tile shows `on`.

2. **IAM sidebar density — 17 flat links** — scrolling required on normal viewports. **Fix:** added `group?: string` to `SubFeatureNav`, reworked `Sidebar` to render group headers. IAM now splits into DIRECTORY (8 links) + SECURITY (9 links) with uppercase section headers. Monitoring same: EXPLORE + ALERTING groups.

### 🟡 Important

3. **Users list: 70+ "—" rows looked broken** — seeded users without EAV email/display_name showed as `?` avatar + `—` name/email, indistinguishable from load failure. **Fix:** fallback now shows `user-<8chars>` in mono italic for missing names, `no email set` italic for missing emails, and UUID first-char in avatar. Users read as "system-created user, no attrs yet" instead of broken UI.

4. **Users list capped at 100** — backend had 122 users; 22 were invisible. **Fix:** raised list fetch to `limit: 500`. Live count shows "123 users" now.

5. **Orgs list had no search** — list unsearchable even at small counts; fine now but would break at 50+ orgs. **Fix:** added `<Input type="search">` that filters by slug or display_name; empty-match shows `<EmptyState>`; count shows "N of M orgs".

## Pages audited as already PRO (no changes needed)

- **Audit Explorer** — timerange filters, category/outcome/actor/metadata filters, totals + category breakdown + time-series, CSV export, live tail, event detail drawer.
- **Feature Flags list** — 6 stat cards, scope + status pill filters, grouped collapsible list, inline active toggle with confirm dialog, search.
- **Roles** — 5 stat cards, platform/org pills, category sections, expandable rows with inline edit + capabilities grid, audit tab, duplicate + delete.
- **Monitoring Logs** — Explorer/Live-Tail tabs, time range pills, severity pills, body search, filters, live log table with relative time.
- **Feature Flag Evaluator** — value + reason Badge + decision trace (override / rule / default).

## Known gaps that remain (future batches)

- **Users list** should offer bulk-delete test users (70+ seeded duplicates exist)
- **Catalog** dense table needs search + feature-filter
- **Auth Policy** uses native Select for booleans; should be Checkbox
- **Orgs row click** uses drawer; would be better as `/iam/orgs/[id]` full page for parity with workspaces and users
- **Monitoring Overview** feature tile grid missing Alerts + Saved Queries cards
- **Notify deliveries retry** UX missing
- **Audit live tail filter passthrough** — filters ignored in live mode
- **Mobile responsive** — sidebar + topbar are still desktop-only
- **Command palette ⌘K** still absent
- **Table sort indicators** — no column-click sort
- **CSV export** on tables beyond Audit

## Verification

- `npx tsc --noEmit` — clean
- Backend restart — `/health` now reports `enabled:7, available:7`
- Browser walkthrough — sidebar groups render on IAM + Monitoring
- Users page — "123 users", fallback IDs visible for seeded test users
- Orgs page — search input present, "4 of 4 orgs" indicator
