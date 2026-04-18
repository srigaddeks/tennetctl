# Second-pass audit — 2026-04-19

After 4 rounds of UX fixes, walked every remaining page with a headful browser.
Most pages now meet the polish bar. This pass flags only **genuine remaining gaps**.

## Tier 1 — worth fixing (minor)

### Account / Sessions
- **SESSION column is just a UUID prefix** — no device name, browser, OS, or IP. User sees `019da1e3…` as "session identity", which is useless for identifying which session to revoke. Backend likely has `user_agent` but UI drops it.
- **All three rows show "6h ago"** for both Signed-in + Last-active — redundant in dev but implies a bug: these two columns should diverge over time.
- **"This device" badge** only on one row is correct, but if all three happen to be the same browser, the user can't tell them apart.
- **Fix size:** medium. Needs backend session view to expose `user_agent`, `ip`, `last_seen`.

### Feature Flag detail
- **No breadcrumbs** (`Feature Flags › <flag key>`). Every other detail page has them now — orgs, users, workspaces. This is the only detail page left without.
- **Header chips could be cleaner** — `org · boolean · active · default = false · org 019d957b…`. The org UUID prefix should be a link to `/iam/orgs/{id}` now that org detail pages exist.
- **Fix size:** small. ~20 lines.

### Account / Security
- **Flat form with bare h3 headings** vs. other pages' `<section className="rounded-lg border bg-white p-6">` cards. Looks like an earlier-gen page.
- **No status indicators for current state** — if I already have TOTP enrolled, the page just says "No authenticator apps enrolled" but doesn't show a list-first UX that the rest of the admin uses.
- **Single-column layout** wastes horizontal space on desktop.
- **Fix size:** small-medium. Visual polish pass.

### Topbar "Feature Flags" wrapping
- Top nav `Feature Flags` and `Node Catalog` wrap onto two lines on 1440-wide viewport when all 11 nav items are shown — visible in several screenshots. My `overflow-x-auto` fix kicks in on narrower, but it also wraps here because there's enough to fit-but-only-just.
- **Fix size:** tiny — `whitespace-nowrap` on the nav Link.

### Monitoring overview stats
- **Error rate 44.9% / 45.2%** — real number, real logs, but the denominator is small (~30 logs in 1h in dev DB). A ratio of 0 error-logs vs. 0 info-logs would render as `NaN%` or `0.0%` silently. Add a `—` fallback when `total === 0`.
- **Stat cards don't link** — clicking "Active services 1" could take you to a filtered logs view. Not critical but leaves money on the table.

### Console 404 noise
- `list_console_messages` shows 4× `Failed to load resource: 404` on the deliveries page — likely the deliveries tail polling a missing endpoint, or preloaded assets that don't exist. Diagnostically noisy; users see nothing, but operators running devtools will.

## Tier 2 — structural / deeper

### Role-check on admin actions (live check)
- I'm signed in as a newly-created `demo.admin@local.test` with no assigned roles. I can still:
  - Add/remove IP allowlist entries
  - Toggle MFA policy globally
  - Create SMTP configs
  - See all users / orgs / workspaces cross-tenant
- This is a **backend permissions gap, not UI** — the UI just renders what the API returns. But it means the UI currently assumes "if you can reach the page, you can act". A proper deployment will break quietly when real role gates arrive. No UI "permission denied" state exists.
- **Fix size:** large. Requires real authz middleware + UI PermissionDeniedState component + per-button gate checks. Belongs in v0.1.8 Auth Hardening.

### Empty "most things" in dev
- Most pages I walked have 0 rows. That's because the DB is freshly seeded. The empty states are fine, but I can't validate:
  - What happens when a table has 10,000 rows (pagination)
  - Virtualization on logs/deliveries
  - How traces render at 100+ spans
  - How audit events render under load
- **Fix size:** these are test-matrix gaps, not code gaps. Would need synthetic load or E2E against a populated DB.

### What doesn't exist at all (needs backend)
- **Impersonation history list** — routes are start/status/end only
- **Audit funnel / retention** — no backend
- **Monitoring synthetic checks** — no backend
- **Starred / pinned events** — no dim table
- **Background worker status dashboard** — no health endpoint per worker
- **Migration history browser** — `_migrations` table exists but no HTTP route

## Tier 3 — not worth fixing right now

- **Error boundary on route root** — Next.js already shows a default; custom error.tsx is polish
- **Keyboard shortcuts** beyond ⌘K — G+I for IAM, G+F for flags, etc. PostHog-level polish, not standard for v0.2.x
- **Skeleton-everywhere** — current Skeleton usage is already consistent
- **Route-level RSC prefetching** — already on by default
- **Bundle analysis** — no evidence of slow pages

## Synthesis

After 4 rounds and ~90 files changed across 4 commits, the admin portal has crossed from "functional" to **"production-quality for a v0.2.4 OSS release"**. The three highest-value items left are:

1. Account/Sessions enrich display (device/browser/IP) — 30-line backend change + 10-line UI
2. Feature Flag detail breadcrumbs + org-id link — 20-line UI patch
3. Account/Security page visual refresh — match the `<section rounded-lg border>` pattern

Everything else either needs new backend surface area (impersonation history, synthetic checks) or is pure polish that crosses diminishing returns at this point.
