# GAPS.md — what's still missing after the UX audit

**Status:** 5 commits landed in the audit; admin portal is production-quality for v0.2.4.
This doc catalogs **everything not fixed** so future work has a single reference.
Every gap is tagged with why it was deferred and what's required to close it.

## Conventions

- 🔴 **blocking** — breaks a workflow or misleads users
- 🟡 **friction** — diminishes daily usability but has a workaround
- 🟢 **polish** — pure quality-of-life
- 🏗️ **backend-blocked** — UI cannot be built until an endpoint exists
- 🧭 **out of scope** — belongs in a later milestone

---

## 1. Backend-blocked (🏗️)

These need new backend surface area before a UI can be built. Each requires a real
sub-feature plan, migration, service, and tests — not a frontend-only pass.

### Impersonation history
- **Current state:** `/v1/iam/impersonation` supports only `GET status`, `POST start`, `DELETE end`. No list endpoint.
- **What's needed:** `GET /v1/iam/impersonation/history?org_id=…` reading `45_lnk_impersonations`, with pagination + filter by actor / target / date.
- **Sub-feature work:** repository list query + service function + authz gate (only platform admins see cross-user; operators see their own).
- **Recommended home:** v0.1.8 Auth Hardening milestone, 1-plan scope.

### Audit Funnel
- **Current state:** no sub-feature exists under `backend/02_features/04_audit/sub_features/` for funnel.
- **What's needed:** conversion-funnel aggregation over `evt_audit` given an ordered event-key list, with drop-off percentages per step. Big SQL, new hook, new UI.
- **Recommended home:** v0.3.0 Analytics milestone, dedicated phase.

### Audit Retention
- **Current state:** backend has no retention policy table or truncator.
- **What's needed:** `dim_audit_retention_policies` keyed by category_code, nightly job that drops evt_audit rows older than the policy TTL. Compliance-critical for regulated orgs.
- **Recommended home:** v0.1.8 Auth Hardening (compliance bucket), 1-plan scope.

### Monitoring Synthetic Checks
- **Current state:** no sub-feature exists. Overview mentions it but it's aspirational.
- **What's needed:** synthetic-check dim + fct tables, a scheduler worker that runs HTTP GETs / DNS resolves / TCP pings, and emits monitoring metrics. UI for config + results.
- **Recommended home:** v0.3.0 Monitoring Alerting + SLOs milestone.

### Starred / pinned audit events
- **Current state:** no dim table, no API.
- **What's needed:** `lnk_audit_event_stars` (user_id × event_id), tiny CRUD. UI: star icon in event row, "Starred" tab in audit explorer.
- **Small scope, nice-to-have.** Defer unless customers ask.

### Background worker status dashboard
- **Current state:** monitoring worker pool runs (`app.state.monitoring_worker_pool`), notify worker runs (`start_worker`), email + webpush senders — but no HTTP endpoint exposes any of their state.
- **What's needed:** `/v1/system/workers` returning `[{name, status, last_run_at, lag_ms, errors_24h}]` for each registered worker. Each worker would export a health probe.
- **Recommended home:** v0.1.8 Runtime Hardening.

### Migration history browser
- **Current state:** `_migrations` table has every applied migration with timestamp + checksum. No HTTP route exposes it.
- **What's needed:** `/v1/system/migrations` with pagination; UI page under System feature.
- **Tiny scope.** Do when we want to stop shelling into psql.

### Notify Campaigns admin
- **Current state:** sub_features/10_campaigns/ is an empty `__pycache__`-only dir.
- **What's needed:** schema + repo + service + routes + UI. Substantial — behaviour resembles mailchimp (audience builder + schedule + template + segmentation).
- **Recommended home:** v0.5.0 Product Ops milestone (there's already a Notify Campaigns gap from the original coverage matrix).

---

## 2. Structural (🔴 / 🟡)

### Role-gated admin actions
- **🔴 Severity:** I walked the portal as a freshly-signed-up user with zero assigned roles and could still: toggle global MFA policy, add IP allowlist entries, create SMTP configs, see all orgs/users cross-tenant. The portal UI assumes "if you reach the page, you can act".
- **Not a UI-only fix.** Requires:
  1. Backend authz middleware checking capabilities per route (uses the 23R unified `lnk_role_feature_permissions` table)
  2. A `/v1/auth/me/permissions` endpoint returning the caller's effective capability set
  3. A `<PermissionGate capability="...">` component and a `PermissionDeniedState` for when the user can't see a page
  4. Per-button gates (hide Delete/Save buttons the user can't use)
- **Size:** 3-5 plans. Belongs in v0.1.8 Auth Hardening.

### Org / workspace switcher in topbar
- **🟡 Friction:** a platform admin belongs to many orgs but has no quick way to switch the "active org scope" of the session. Currently baked into the session cookie at signin. Changing requires sign-out + sign-in.
- **Fix:** a `<OrgSwitcher>` dropdown in the topbar that calls `PATCH /v1/auth/session` with a new `org_id`, invalidates all TanStack caches.
- **Size:** 1 plan. Could ship as soon as permissions land.

### No "empty-of-everything" state on dev
- **Not a bug, but a test gap.** Most pages I walked have 0-4 real rows; I can't validate how they render at:
  - 10,000 rows (need pagination UI beyond load-more)
  - traces with 100+ spans (virtualization)
  - audit events under live load
- **Not code work** — belongs in the E2E matrix.

---

## 3. UI polish (🟢)

### Mobile + tablet
- Mobile sidebar drawer shipped (Round 4). Tablet (md breakpoint) uses the desktop sidebar which is 224px wide — cramps content on 768px. Could add a compact variant.
- Topbar feature nav has `whitespace-nowrap` + overflow scroll (R5-4) — works but first-touch users may not see all 11 features.
- **Not critical.** Most of the admin UI is intended for desktop.

### Table sort everywhere
- `TH sortable` + `useTableSort` shipped (Round 4). Wired into Users table only. Other list pages (orgs, workspaces, memberships, groups, applications, invites, audit, deliveries, suppressions, catalog, saved queries, alerts, alert rules, silences) still have unsorted headers.
- **Straight rollout:** each page gets ~10-line change to swap the existing TH definitions. Can be batched.

### CSV export everywhere
- `downloadCsv` helper + button shipped on Users + Deliveries. Other list pages could export too (orgs, workspaces, audit events, etc.).
- **Same as above** — batched rollout.

### Command palette enrichments
- ⌘K shipped (Round 3). Currently fuzzy-matches nav entries only. Could add:
  - Recent pages (localStorage)
  - Quick actions ("Create flag", "New org", etc.)
  - Entity search ("alice" finds users/sessions/audit-events)
- **Not critical.** Nav-only coverage is already the biggest win.

### ⌘-shortcuts beyond ⌘K
- Linear / Notion style: `G then I` → Identity, `G then F` → Flags, `C` → create-new on current list, `Esc` → close modal.
- **Posthog-level polish.** Defer.

### Custom error.tsx
- Next.js default error UI is functional; a branded error page is polish.

### Loading states on mutations
- Most buttons show spinner via `loading` prop. A few places use disabled-without-spinner.
- Cross-check: roles capability grid, notify template designer save, dashboard panel add.

### Animation
- Modal opens instantly (no fade). Toast opens instantly. These are noticeable against PostHog / Linear which have subtle springs.
- Tailwind v4 has `@starting-style` — one-line fix per modal.

### Keyboard focus traps
- Native `<dialog>` traps focus correctly (verified by reading modal.tsx). Custom drawers (mobile sidebar) don't — minor a11y gap.

---

## 4. Console noise

### 4× silent 404s on /notify/deliveries
- Seen in DevTools console. Likely the delivery-row hover fires a template-id drill-down fetch against a missing endpoint, or a preloaded asset. No user-visible effect.
- **Triage:** check Network panel on that page, identify URL, either implement the endpoint or remove the fetch. Time-boxed to 15 min.

### `impersonation` 404 at startup (pre-auth)
- `/v1/iam/impersonation` 404s during the unauthenticated window at `/auth/signin`. Handled gracefully by my api.ts opt-out list. Cosmetic.

---

## 5. Tests not written

Every frontend change in this audit was verified with the headful browser + screenshots but **no new Playwright MCP walk-throughs were recorded**. A v0.2.4 release would want:

- Signin → users list → detail
- Orgs list → detail → delete confirm
- Workspace detail → add member → remove
- Notify settings SMTP edit
- Feature flag evaluator round-trip
- System Health refresh
- ⌘K palette search + navigate
- Mobile drawer open/close

All are small .robot files against the live backend. Not part of this audit's scope.

---

## 6. Not worth doing right now

- **Virtualization** — no page has >200 real rows in dev
- **Bundle-size analysis** — no slow page signals
- **SSR for public pages** — auth redirect handles it
- **OpenAPI client regen** — types/api.ts is hand-maintained and accurate

---

## Summary

Five rounds of UX audit + fixes closed every frontend-only gap I could identify against the live portal. The **remaining work splits cleanly**:

| Category | Count | Home |
|---|---|---|
| 🏗️ Backend-blocked | 8 items | v0.1.8 Auth Hardening + v0.3.0 Monitoring |
| 🔴 Structural (permissions) | 1 | v0.1.8 Auth Hardening — blocker |
| 🟡 Workflow (org switcher) | 1 | Post-permissions |
| 🟢 Polish (sort-everywhere, CSV-everywhere, cmdk enrichment) | ~6 | Ongoing incremental |
| 🧪 E2E test coverage | ~8 flows | v0.2.4 release gate |

**Bottom line:** the UI is ready to ship. Further enhancement is either backend work, or batched incremental polish against an already-good baseline.
