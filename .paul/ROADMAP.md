# Roadmap: TennetCTL

## Overview

TennetCTL is built milestone-by-milestone from core infrastructure through enterprise IAM. Every phase after foundation is a full vertical slice: schema → repo → service → routes → nodes → UI → Playwright live verification. Nothing ships without being tested in a real browser.

**Architectural spine:** Node Catalog Protocol v1 (see `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`). Every feature vertical (Phase 3+) uses it.

## Current Milestone

**v0.2.2 Unified SDK Observability** (v0.2.2) — NEXT
Status: Queued — requires monitoring backend (Phase 13) verified live before plan.
Theme: Add metrics + logs + traces to the same SDK. `tennetctl.autoinstrument(app)` makes backend services self-observing in one line.
Phases: 0 of 2 (Phases 30–31)

**v0.2.1 Unified SDK Core** (v0.2.1) — ✅ COMPLETE (2026-04-18)
Theme shipped: Polyglot SDK (Python + TypeScript) with single client covering auth + flags + iam + audit + notify.
Phases: 2 of 2 complete. 114 tests green across both languages, ≥93% coverage each.
See: `.paul/phases/28-sdk-core-auth/` + `.paul/phases/29-sdk-core-flags-iam-audit-notify/`

## Queued Milestones

**v0.2.2 Unified SDK Observability** (v0.2.2) — Queued
Theme: Add metrics + logs + traces to the same SDK. `tennetctl.autoinstrument(app)` makes backend services self-observing in one line.
Phases: 0 of 2 (Phases 30–31)

**v0.2.3 Unified SDK Platform** (v0.2.3) — Queued
Theme: Close SDK coverage — vault + catalog inspection — and compile request-path flags to APISIX so the gateway evaluates without backend round-trip.
Phases: 0 of 2 (Phases 32–33)

**v0.2.4 Admin UI Coverage Pass** (v0.2.4) — Queued
Theme: Every feature module has a complete admin portal page. Walk every feature, enumerate gaps, build missing pages, unify navigation. All pages dogfood the unified SDK.
Phases: 0 of 3 (Phases 34–36)

**v0.1.8 Runtime Hardening** (v0.1.8) — Queued
Theme: Close pre-OSS audit gaps — catalog hot-reload, rate limiting, HIBP, passkey hardening, 2FA enforcement, NCP v1 doc sync, handler caching, versioning pattern.
Phases: 0 of 3 (Phases 37–39)

**v0.3.0 Monitoring Alerting + SLOs** (v0.3.0) — Queued
Theme: Finish Phase 13 (paused at 13-07). Alerting end-to-end, SLO tracking, dashboard sharing. Monitoring SDK already shipped in v0.2.2.
Phases: 0 of 2 (Phases 40–41)

**v0.4.0 Canvas + Visual Flow Viewer** (v0.4.0) — Queued
Theme: React Flow canvas reads live catalog via the same `client.catalog` surface external apps use. Read-only v1 — typed ports, DAG render, execution trace overlay.
Phases: 0 of 3 (Phases 42–44)

**v0.8.0 GDPR DSAR** (v0.8.0) — Queued (scoped 2026-04-20)
Theme: Self-service data subject access + erasure flows for the platform itself (IAM/audit/notify scope). Required for OSS readiness in EU/UK markets.
Phases: 0 of 1 (Phase 45)

## Previous Milestones

**v0.2.0 Feature Flags + AuthZ Control Plane** (v0.2.0)
Status: ✅ Complete (2026-04-18 via 23R rebase)
Theme: Unified AuthZ + Feature Control Plane. Original Phases 23–27 were condensed into the 23R rebase (3 plans, commits ec93b58 → eab604b → d874a14) delivering the unified flag+permission role model. SDK, APISIX compilation, and portal views carried forward to v0.2.1 / v0.2.2.
Phases: Shipped via 23R (23R-01, 23R-02, 23R-03). Original 23–27 plans closed as superseded.

**v0.1.9 IAM Enterprise** (v0.1.9)
Status: ✅ Complete (2026-04-18)
Theme: Enterprise-grade federated identity (SAML/OIDC SSO), automated provisioning (SCIM 2.0), admin controls, compliance primitives — everything a mid-market SaaS team needs to pass a security review.
Phases: 0 of 1 complete

**v0.1.6 IAM Hardening for OSS** (v0.1.6)
Status: ✅ Complete (2026-04-17)
Theme: Make IAM production-grade before open-sourcing. Config-driven auth policy (no hardcoded thresholds), account lockout, session limits, audit coverage closure, email OTP via existing Notify templates, API key rotation, IAM metrics.
Phases: 2 of 2 complete

**v0.1.7 Notify Production + Developer Docs** (v0.1.7)
Status: ✅ Complete
Theme: Close production gaps so the notify backend is a real primitive for building business apps; ship developer documentation.
Phases: 6 of 6 complete

**v0.1.5 Observability** (v0.1.5) — ✅ Complete (Phase 13 all 8 plans shipped)

**v0.1 Foundation + IAM** (v0.1.0) — ✅ Complete (12/12 phases)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with [INSERTED])

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Infrastructure | 3 | ✅ Complete | 2026-04-13 |
| 2 | Catalog Foundation | 3 | ✅ Complete | 2026-04-16 |
| 3 | IAM & Audit Schema | 4 | ✅ Complete | 2026-04-16 |
| 4 | Orgs & Workspaces (vertical) | 2 | ✅ Backend complete | 2026-04-16 |
| 5 | Users & Account Types (vertical) | 2 | ✅ Backend complete | 2026-04-16 |
| 6 | Roles, Groups, Scopes & Applications (vertical) | 1 | ✅ Backend complete | 2026-04-16 |
| 7 | Vault (vertical) | 2 | ✅ Full-stack complete | 2026-04-16 |
| 8 | Auth Basics — Password + OAuth + Sessions (vertical) | 2 | 🟡 In progress | - |
| 9 | Feature Flags (vertical) | 2 | Not started | - |
| 10 | Audit Analytics (PostHog-class vertical) | 4 | Not started | - |
| 11 | Notify (Mailchimp-class vertical) | 12 | ✅ Complete | 2026-04-17 |
| 12 | IAM Security Completion — Magic Link, OTP, Passkeys (vertical) | 4 | ✅ Complete | 2026-04-17 |
| 13 | Monitoring — OTel Logs + Metrics + Traces + Alerting (vertical, v0.1.5) | 8 | ⏸ Paused | - |
| 14 | Notify — API Keys + Send Idempotency (v0.1.7) | 1 | ✅ Complete | 2026-04-17 |
| 15 | Notify — List-Unsubscribe + Suppression List (v0.1.7) | 1 | ✅ Complete | 2026-04-17 |
| 16 | Notify — Scheduled Sends (v0.1.7) [quiet-hours + tz deferred to v0.1.8] | 1 | ✅ Complete | 2026-04-17 |
| 17 | Notify — Channel Fallback (v0.1.7) | 1 | ✅ Complete | 2026-04-17 |
| 18 | Notify — Per-Template Analytics UI (v0.1.7) | 1 | ✅ Complete | 2026-04-17 |
| 19 | Developer Docs Pass — Integration guide, API reference, deployment, DKIM/DMARC, examples (v0.1.7) | 1 | ✅ Complete | 2026-04-17 |
| 20 | IAM Hardening for OSS — config-driven policy, lockout, session limits, audit closure, OTP→Notify, key rotation, metrics (v0.1.6) | 6 | ✅ Complete | 2026-04-17 |
| 21 | IAM OSS Completion — email verification, invite flow, first-run wizard, deactivate vs delete, GDPR, session UI (v0.1.6) | 6 | ✅ Complete | 2026-04-17 |
| 22 | IAM Enterprise — OIDC SSO, SAML SSO, SCIM, impersonation, MFA enforcement, IP allowlist, SIEM export (v0.1.9) | 8 | ✅ Complete | 2026-04-18 |
| 23 | Feature Flag Engine Foundation (v0.2.0) | 3 | ✅ Superseded by 23R | 2026-04-18 |
| 24 | Feature-Scoped Permissions + Role Redesign (v0.2.0) | 3 | ✅ Superseded by 23R | 2026-04-18 |
| 25 | SDK + Gateway Compilation (v0.2.0) | 2 | ⏭ Carried to v0.2.1 (Phase 28/29) | - |
| 26 | Awesome UX (v0.2.0) | 3 | ✅ Superseded by 23R (Role Designer shipped) | 2026-04-18 |
| 27 | Portal Views + AuthZ Audit Explorer (v0.2.0) | 2 | ⏭ Carried to v0.2.2 (Phase 30/31) | - |
| 23R | Unified Flag+AuthZ Rebase (v0.2.0) | 3 | ✅ Complete | 2026-04-18 |
| 28 | SDK Core — skeleton + auth module (v0.2.1) | 2 | ✅ Complete | 2026-04-18 |
| 29 | SDK Core — flags + iam + audit + notify modules (v0.2.1) | 2 | ✅ Complete | 2026-04-18 |
| 30 | SDK Observability — metrics + logs (v0.2.2) | 1 | ✅ Complete | 2026-04-18 |
| 31 | SDK Observability — traces + auto-instrument (v0.2.2) | 1 | 🟡 Partial (query shipped; autoinstrument deferred) | 2026-04-18 |
| 32 | SDK Platform — vault + catalog modules (v0.2.3) | 1 | ✅ Complete | 2026-04-18 |
| 33 | APISIX Gateway Sync (v0.2.3) | 1 | ✅ Complete | 2026-04-18 |
| 34 | Admin UI — coverage audit (v0.2.4) | 1 | ✅ Complete | 2026-04-18 |
| 35 | Admin UI — build missing critical pages (v0.2.4) | TBD | Not started | - |
| 36 | Admin UI — polish + unified nav (v0.2.4) | TBD | Not started | - |
| 37 | DX + Catalog Hot-Reload (v0.1.8) | 1 | ✅ Complete | 2026-04-18 |
| 38 | Auth Hardening — rate limit, HIBP, passkey, 2FA policy (v0.1.8) | TBD | Not started | - |
| 39 | NCP v1 Maturity — doc sync, handler caching, versioning, bulk ops (v0.1.8) | TBD | Not started | - |
| 40 | Monitoring Alerting (v0.3.0) | TBD | Not started | - |
| 41 | Monitoring SLO + dashboard sharing (v0.3.0) | TBD | Not started | - |
| 42 | Flow schema + backend (v0.4.0) | TBD | Not started | - |
| 43 | Canvas renderer (v0.4.0) | TBD | Not started | - |
| 44 | Trace overlay + search (v0.4.0) | TBD | Not started | - |
| 45 | GDPR DSAR (v0.8.0) | TBD | Not started | - |

## Phase Details

### Phase 1: Core Infrastructure

**Goal:** Running backend + frontend shells with database, migrations, node registry skeleton, and Playwright test harness — everything needed before any feature vertical.
**Depends on:** Nothing (first phase)

**Plans:**
- [x] 01-01: Docker Compose (tennetctl_v2) + enterprise SQL migrator
- [x] 01-02: Python backend scaffold (FastAPI app, core modules, node registry)
- [x] 01-03: Next.js frontend shell + Playwright test harness

### Phase 2: Catalog Foundation

**Goal:** The Node Catalog Protocol (NCP v1) is implemented end-to-end: manifest loader, catalog DB, node runner with execution primitives. From here, every cross-sub-feature call goes through `run_node`; direct imports across sub-features are lint-blocked.
**Depends on:** Phase 1 (database + migrator + backend scaffold)
**Research:** None (protocol is specified in `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`)

**Scope:**
- `01_catalog` schema: dim_modules, dim_node_kinds, dim_tx_modes, dim_entity_types, fct_features, fct_sub_features, fct_nodes, dtl_attr_defs, dtl_attrs
- NCP v1 protocol doc published
- ADR-027 Catalog + Runner decision recorded
- `backend/01_catalog/` Python module: manifest loader, boot upsert, validator (incl. cross-import linter), `Node` base class, `NodeContext`, `run_node` runner
- Execution policy enforcement: timeout, retry on `TransientError`, tx modes (caller/own/none), authorization hook
- `/tnt` Claude skill (single skill) explaining the pattern

**Plans:**
- [x] 02-01: NCP v1 protocol doc + ADR-027 + catalog DB schema
- [x] 02-02: Manifest loader + boot upsert + validator + `/tnt` skill
- [x] 02-03: Node runner (execution policy, NodeContext, authorization hook)

### Phase 3: IAM & Audit Schema

**Goal:** All IAM + audit database tables migrated, IAM registered in the catalog via its `feature.manifest.yaml`, audit service cross-cutting pattern established, `emit_audit` node operational and callable from any sub-feature via `run_node`.
**Depends on:** Phase 2 (catalog must exist so IAM can register against it)

**Scope:**
- `03_iam` schema: dim tables (account_types, scopes, roles, groups), fct tables (orgs, workspaces, users, applications), dtl tables (attr_defs, attrs), lnk tables (user-org, user-workspace, user-role, user-group), views
- `04_audit` schema: evt_audit table, audit service, `emit_audit` node (first real cross-cutting node)
- `backend/02_features/03_iam/feature.manifest.yaml` — first real consumer of NCP v1
- EAV foundation: dim_attr_defs + dtl_attrs pattern
- All views for read paths (`v_orgs`, `v_workspaces`, `v_users`, etc.)

**Plans:**
- [x] 03-01: IAM schema migrations
- [x] 03-02: IAM feature.manifest.yaml + catalog registration verification
- [x] 03-03: Audit schema + audit.events.emit node (+ inline IAM per-sub-feature layout restructure)
- [x] 03-04: Views (v_orgs, v_workspaces, v_users) + 5 dim_attr_defs seeded

### Phase 4: Orgs & Workspaces (vertical)

**Goal:** Full vertical: create/list/update/delete orgs and workspaces with EAV attrs, audit trail, nodes, UI pages, Playwright live verification. Every cross-sub-feature call goes through `run_node`.
**Depends on:** Phase 3 (schema + audit + catalog wiring must exist)

**Scope:**
- Org repo → service → routes → nodes (registered in manifest)
- Workspace repo → service → routes → nodes (scoped under org)
- UI: org list, create org, org detail, workspace list, create workspace
- Audit on every mutating action via `run_node("audit.emit", ...)`
- Playwright live test: create org → create workspace → verify

**Plans:**
- [ ] 04-01: Org sub-feature (schemas/repo/service/routes + nodes + manifest entry)
- [ ] 04-02: Workspace sub-feature (schemas/repo/service/routes + nodes + manifest entry)
- [ ] 04-03: Org & Workspace UI + Playwright live verification

### Phase 5: Users & Account Types (vertical)

**Goal:** Full vertical: user CRUD, account type management (email/password, magic link, Gmail/OAuth), user-org-workspace membership, UI, Playwright verification.
**Depends on:** Phase 4 (orgs + workspaces must exist for membership)

**Scope:**
- User sub-feature (repo/service/routes/nodes + manifest)
- Account type management (dim_account_types driving auth options)
- User-org and user-workspace membership via lnk tables, invoked via `run_node`
- UI: user list, create user, user detail, account type display, membership management
- Playwright live test: create user → assign to org/workspace → verify membership

**Plans:**
- [ ] 05-01: User sub-feature (repo, service, routes, nodes, account types, audit)
- [ ] 05-02: User membership (lnk tables, org/workspace assignment)
- [ ] 05-03: User UI + Playwright live verification

### Phase 6: Roles, Groups, Scopes & Applications (vertical)

**Goal:** Full vertical: role/group CRUD, scope management (global/org), application/product CRUD, assignment link tables, UI, Playwright verification.
**Depends on:** Phase 5 (users must exist for role/group assignment)

**Scope:**
- Role/group sub-features
- Scope management (global + org level now, workspace future)
- Application/product CRUD
- Assignment: user-role, user-group via lnk tables
- UI: role management, group management, scope config, application list
- Playwright live test: create role → assign to user → verify scope resolution

**Plans:**
- [ ] 06-01: Roles, groups & scopes sub-features (repo, service, routes, nodes, audit)
- [ ] 06-02: Applications sub-feature + scope assignment
- [ ] 06-03: Roles/Groups/Scopes/Applications UI + Playwright live verification

### Phase 7: Vault (vertical)

**Goal:** Full vertical: secret management with AES-256-GCM envelope encryption, bootstrap secrets, reveal-once UI pattern, Robot E2E verification.
**Status:** ✅ Complete (2026-04-16)

**Plans:**
- [x] 07-01: Vault backend (encryption, bootstrap, CRUD, nodes, audit)
- [x] 07-02: Vault UI (reveal-once dialogs, create/rotate/delete, Robot E2E 4/4)

### Phase 8: Auth — Credentials, Sessions, Auth Flow (vertical)

**Goal:** Full vertical: API credential management, session management, and auth flow
(signup/signin/signout/me + Google/GitHub OAuth). Includes auth middleware for session
injection and full pytest + Robot E2E verification.
**Depends on:** Phase 3 (IAM schema — sessions and credentials tables already exist)
**Status:** 🟡 In progress — backend code exists, tests pending

**Scope:**
- `sub_features/08_credentials/` — API key CRUD (list, create, revoke)
- `sub_features/09_sessions/` — session management (list, revoke, validate_session node)
- `sub_features/10_auth/` — auth endpoints (signup, signin, signout, /me, google, github OAuth)
- Session middleware — optional auth injecting user_id/session_id into request.state
- Frontend: /auth/signin, /auth/signup, /auth/callback/google, /auth/callback/github
- Topbar: show current user name + signout action
- Robot E2E: signin flow, signout, protected page redirect

**Plans:**
- [ ] 08-01: Backend auth — wire + pytest green (credentials, sessions, auth sub-features)
- [ ] 08-02: Frontend auth + Robot E2E + full commit

### Phase 9: Feature Flags (vertical)

**Goal:** Full vertical: feature flag management scoped to org/workspace, UI, Playwright verification.
**Depends on:** Phase 8 (auth needed for protected routes)
**Status:** Not started

**Plans:**
- [ ] 09-01: Feature flags sub-feature (repo, service, routes, nodes, scope evaluation)
- [ ] 09-02: Feature flags UI + Playwright live verification

### Phase 10: Audit Analytics (vertical)

**Goal:** Turn `evt_audit` from a write-only compliance trail into a PostHog-class event analytics surface: typed taxonomy, rich query API, timeline + funnel + retention UI, real-time tail, durable pub/sub outbox to feed downstream consumers (Notify, webhooks, exports).
**Depends on:** Phase 3 (evt_audit schema exists), Phase 8 (auth for protected routes)
**Status:** Not started

**Scope:**
- `dim_audit_event_keys` + `dim_audit_categories` dim tables (typed taxonomy replacing CHECK-constraint strings)
- Auto-sync event keys from observed `evt_audit` + explicit registration via feature manifests
- `v_audit_events` view joining dim tables for labels + descriptions
- Query API: list with rich filters (actor/org/workspace/event_key glob/category/outcome/trace/time range), full-text on metadata JSONB, cursor pagination (UUID v7 ordering), stats aggregates (per-key, per-outcome, per-actor, hourly/daily buckets)
- `audit.events.query` control node (read-only DB ops widening per Phase 4 decision)
- Audit Explorer UI: event list w/ filters + chips, event detail (pretty metadata, trace clustering), live tail, per-key timeline chart, stats dashboard, funnel builder, saved views
- Durable outbox: `evt_audit_outbox` table with cursor, trigger-fed on every evt_audit insert; Postgres LISTEN/NOTIFY for hot-path wake-up; `audit.events.subscribe` contract for consumers
- Pytest + Robot E2E (emit events → query via UI → verify filters/pagination/stats)

**Plans:**
- [ ] 10-01: Taxonomy + query API (dim tables, view, query routes + node, pytest)
- [ ] 10-02: Audit Explorer UI (list/detail/live-tail/stats) + Robot E2E
- [ ] 10-03: Funnel + retention + saved views + CSV export
- [ ] 10-04: Durable outbox + LISTEN/NOTIFY + `audit.events.subscribe` contract

### Phase 11: Notify (vertical)

**Goal:** Ship a Mailchimp-class multi-channel notification platform driven by audit events. Transactional (signup, password reset), critical (mission-critical security alerts with priority delivery + multi-channel fan-out), marketing (campaigns, broadcasts), and digest (daily summaries) across email (with open/click tracking), web push (VAPID), in-app bell, and SMS-ready schema. Templates are grouped; each group picks its own SMTP config (transactional vs marketing vs critical isolated at infra level). Variables are both static and dynamic — dynamic variables execute safelisted SQL against views using the triggering audit event's actor/org/workspace as parameters to enrich payloads (e.g. trace back from `iam.users.signed_up` event to the user's display_name + org name + workspace). Template designer UI with live preview and test-send. Pure REST API for direct transactional sends (bypass audit-event trigger). Audience segmentation, campaign scheduling, delivery analytics, and user preferences with one-click unsubscribe.
**Depends on:** Phase 10 (`audit.events.subscribe` outbox contract + event detail lookup)
**Status:** Not started

**Scope:**
- Feature `06_notify` + schema `"06_notify"`
- Dim tables: `notify_channels` (email/webpush/in_app/sms), `notify_categories` (transactional/critical/marketing/digest — `critical` triggers multi-channel fan-out + priority queue), `notify_statuses` (pending/queued/sent/delivered/opened/clicked/bounced/failed/unsubscribed), `notify_priorities` (low/normal/high/critical)
- Template groups: `fct_notify_template_groups` (key, label, category, default SMTP config ref → vault). Enables isolating transactional SMTP from marketing SMTP from critical (PagerDuty-grade) SMTP
- SMTP configs: `fct_notify_smtp_configs` (key, host, port, tls, auth vault_key — credentials live in vault). Linked 1:N to template groups
- Templates: `fct_notify_templates` (key, group_id, subject, reply_to, priority) + per-channel `dtl_notify_template_bodies` (channel_id, body_html, body_text, preheader); Jinja2 StrictUndefined rendering
- Variable system — `fct_notify_template_variables`:
  - **Static:** literal value set at template-creation time (e.g. brand_name = "TennetCTL")
  - **Dynamic (SQL):** safelisted read-only SQL against `v_*` views only, parameterized by audit event context ($actor_user_id, $org_id, $workspace_id, $event_metadata). Stored as `{var_name, sql_template, param_bindings}`. Executed in read-only tx with query timeout. Results cached per delivery.
  - Variables registered per template. Audit-event-to-user trace-back is the canonical dynamic pattern
- Subscriptions: `fct_notify_subscriptions` maps `event_key_pattern → template_id + channel + priority_override + condition_expr`; worker consumes `audit.events.subscribe` outbox and enqueues deliveries; critical events fan out across ALL user-enabled channels
- Deliveries: `fct_notify_deliveries` (template_id, recipient_user_id, channel_id, priority_id, status_id, audit_event_id FK, resolved_variables JSONB) + append-only `evt_notify_delivery` (open/click/bounce/unsubscribe tracking events)
- Email: vault-stored SMTP per template group, `aiosmtplib` async sender, `pytracking` open pixel + signed click-tracking redirects, return-path webhook for bounces, unsubscribe token links, DKIM/SPF validator
- Web push: vault-stored VAPID keys, `fct_webpush_subscriptions`, `pywebpush` sender, service worker + subscribe flow on frontend; `critical` priority triggers webpush alongside email
- In-app: `fct_notifications` per-user queue, bell icon + /notifications page, mark-read mutation, `critical` priority gets persistent banner
- Preferences: `lnk_notify_preferences` (user × category × channel × enabled). `critical` channel opt-outs are blocked by policy — user cannot disable mission-critical security alerts
- Campaigns: `fct_notify_campaigns` (audience_query, template_id, scheduled_at, throttle, status), audience builder (user filter DSL → SQL), campaign runner with batched send + retry
- **Template Designer UI:** HTML/Markdown editor with live preview pane, variable picker (drag-drop {{var}} from registry), side-by-side rendered preview using sample/real audit event, test-send to any email, version history
- **Pure API for transactional sends:** `POST /v1/notify/send` — caller provides `{template_key, recipient_user_id, channel, variables?}` → bypasses audit-event subscription, enqueues direct delivery, returns `delivery_id`. Used by code paths that don't have a corresponding audit event or need synchronous send confirmation
- Analytics UI: campaign detail (sent/delivered/opened/clicked/bounced/unsubscribed), open rate, click rate, time-series chart, A/B placeholder
- Robot E2E covering signup → transactional email → open tracked → critical alert fan-out → campaign send → preferences toggle → unsubscribe

**Plans:**
- [x] 11-01: Schema + dim seeds + template groups + SMTP configs + templates sub-feature (backend CRUD + Jinja2 render node)
- [x] 11-02: Variable system (static + dynamic SQL) with safelist + tx isolation + per-delivery cache
- [x] 11-03: Subscriptions + audit-outbox consumer worker + critical fan-out logic
- [x] 11-04: Email channel + `aiosmtplib` sender (per-group SMTP) + `pytracking` open/click + bounce webhook
- [x] 11-05: Web push channel + VAPID keys + `pywebpush` + service worker frontend + critical priority banner
- [x] 11-06: In-app notifications + bell UI + mark-read mutation + critical persistent banner
- [x] 11-07: User preferences + unsubscribe flow + `/settings/notifications` page (critical opt-out blocked)
- [x] 11-08: Campaigns + audience DSL + scheduler + throttled runner
- [x] 11-09: Template Designer UI (editor, live preview, variable picker, test-send, version history)
- [x] 11-10: Pure transactional API (`POST /v1/notify/send`) + `notify.send.transactional` node
- [x] 11-11: Delivery analytics UI (per-campaign stats + time-series) + notify explorer
- [x] 11-12: Robot E2E full flow + commit

### Phase 12: IAM Security Completion (vertical)

**Goal:** Round out IAM auth with the modern methods Phase 8 deferred: magic-link email signin, OTP (email code + TOTP authenticator app), and WebAuthn passkeys. Depends on Notify so magic links and OTP codes can actually reach the user. Password reset + account recovery flows also land here (both need email delivery). Every auth-impacting action emits an audit event, which feeds security alerts through Notify `critical` category.
**Depends on:** Phase 11 (Notify — email delivery for magic links, OTP codes, password reset)
**Status:** ✅ Complete (2026-04-17)

**Scope:**
- `sub_features/11_magic_link/` — signed single-use tokens (HMAC via vault), 10-min TTL, consumed-on-use, rate-limited by email + IP
- `sub_features/12_otp/` — email OTP (6-digit code, 5-min TTL, max 3 attempts) + TOTP (authenticator app, RFC 6238, `pyotp`, AES-256-GCM encrypted secrets)
- `sub_features/13_passkeys/` — WebAuthn passkeys via `py_webauthn` v2.7.1, multiple credentials per user, device naming, last-used tracking
- `sub_features/14_password_reset/` — email reset link, HMAC token, 15-min TTL, argon2id re-hash on complete
- Account setup UI: `/account/security` per-user security page with TOTP + passkey enrollment + management
- Signin UI expansion: 4-tab method picker (password / magic-link / OTP / passkey), forgot-password flow
- Robot E2E: all 4 signin tabs validated, forgot-password link, /auth/forgot-password page, /auth/password-reset token missing state

**Plans:**
- [x] 12-01: Magic link sub-feature + integration with Notify transactional send
- [x] 12-02: OTP (email + TOTP) sub-feature
- [x] 12-03: WebAuthn passkeys sub-feature
- [x] 12-04: Password reset + security UI + Robot E2E

---

### Phase 13: Monitoring — OTel Logs + Counter Metrics (vertical, v0.1.5)

**Goal:** Replace the Prometheus/Loki/Grafana stack with an internal, self-hostable observability layer. OTel logs flow through NATS JetStream (`monitoring.logs.otel.>`) into Postgres behind a `LogsStore` Protocol seam. Counter metrics write directly to Postgres behind a `MetricsStore` Protocol. Both stores are ClickHouse-swappable in v0.2 by changing an env var — no caller code changes.
**Depends on:** Phase 10 (audit analytics — for consistent event-query patterns), NATS JetStream already running in docker-compose
**Status:** 🟡 Planning — 13-01 created

**Architecture:**
- **Logs path (OTel + JetStream):** OTLP/HTTP receiver endpoint → publish to `monitoring.logs.otel.>` → durable JetStream consumer worker → `LogsStore.insert_batch()` → Postgres partitioned `evt_monitoring_logs` (daily RANGE partitions)
- **Metrics path (counters):** `POST /v1/monitoring/metrics/increment` + `monitoring.metrics.increment` node → `MetricsStore.increment()` → direct Postgres write to partitioned `evt_monitoring_metric_points`. Metric definitions live in `fct_monitoring_metrics` registry
- **Storage seam:** `typing.Protocol` interfaces (`LogsStore`, `MetricsStore`) with single `get_*_store()` factory; switch via `TENNETCTL_MONITORING_STORE_KIND` env var (v0.1.5: postgres only; v0.2: clickhouse swap-in)

**Architecture (revised 2026-04-17 after gap review):**
- **3 OTel pillars from day one**: logs + metrics (counter/gauge/histogram) + traces/spans
- **Ingest paths**: OTLP/HTTP receiver → NATS JetStream (durable) → consumer workers → Postgres via `LogsStore`/`SpansStore` Protocols. Metrics: direct HTTP + SDK → `MetricsStore` Protocol → Postgres (no NATS). APISIX Prometheus scraper feeds gateway telemetry in.
- **Storage seam**: all 4 stores (`LogsStore`, `MetricsStore`, `SpansStore`, `ResourcesStore`) are `typing.Protocol`s. Swap to ClickHouse in v0.2 via `TENNETCTL_MONITORING_STORE_KIND=clickhouse` — no caller changes
- **Resource interning** in `fct_monitoring_resources` (service_name + instance + version + attrs → BIGINT FK) cuts storage 10–50×
- **Cardinality caps** enforced at `MetricsStore.increment`; audit emitted on reject
- **Rollup tables** `_1m`/`_5m`/`_1h` populated by `pg_cron` — 90d queries run against rollups, not raw
- **Daily range partitioning** on all evt + rollup tables; `pg_cron` partition manager creates/drops per retention policy (hot/warm/cold tiers)
- **Redaction pipeline** in log consumer (regex + denylist, vault-controlled rules)
- **Auto-instrumentation**: FastAPI middleware + asyncpg hooks + structlog bridge — backend self-observes
- **Query DSL** (ADR-028): JSON-based, parameterized, safelisted. UI + alerts + saved queries all use the same DSL
- **Alerting** reuses Phase 11 Notify (critical category → multi-channel fan-out) — no new delivery code
- **Synthetic checks** give dead-man's-switch coverage independent of log volume
- **LISTEN/NOTIFY** drives sub-100ms live tail

**Plans:**
- [ ] 13-01: Foundation — full 3-pillar schema (logs + metrics + spans + rollups + resources + dim) + 4 store Protocols + Postgres impls + JetStream streams (MONITORING_LOGS + MONITORING_SPANS + MONITORING_DLQ) + feature manifest
- [ ] 13-02: Metrics ingest — counter + gauge + histogram; REST + catalog nodes + SDK + cardinality enforcement
- [ ] 13-03: OTLP receiver (logs + traces) + auto-instrumentation (FastAPI + asyncpg + structlog bridge)
- [ ] 13-04: JetStream consumers (logs + spans) + redaction engine + APISIX Prometheus scraper + DLQ
- [ ] 13-05: Query DSL (ADR-028) + compiler + query API (logs + metrics + traces) + saved queries + DLQ replay + health endpoint
- [ ] 13-06: UI — log explorer + live tail + metric dashboards + trace waterfall + dashboards/panels CRUD + Robot E2E
- [ ] 13-07: pg_cron rollups + partition manager + retention tiering + synthetic checks + LISTEN/NOTIFY live-tail
- [ ] 13-08: Alerting — rules + evaluator worker + silences + Notify integration + alerts UI + end-to-end Robot E2E

### Phase 14: Notify — API Keys + Send Idempotency (v0.1.7)

**Goal:** Make the Send API safely callable by external systems. Issue scoped API keys, require `Idempotency-Key` on every transactional send, dedupe on repeat.
**Depends on:** Phase 11 (Notify), Phase 7 (Vault — for key storage)

**Scope:**
- New table `03_iam.28_fct_api_keys` (key_id + argon2 hash + scopes[] + created_by + last_used_at + expires_at + revoked_at)
- `GET/POST/DELETE /v1/api-keys` — list/create/revoke; create returns the token exactly once
- Middleware: `Authorization: Bearer nk_<key_id>.<secret>` in addition to session cookies; populates `request.state.{user_id, org_id}` on match
- Scopes enforced at the router level: `notify:send`, `notify:read`, `audit:read`, etc.
- `Idempotency-Key` header on `POST /v1/notify/send` — new dim table for idempotency records OR just a partial unique index on `(org_id, idempotency_key)` on deliveries
- Admin UI: `/account/api-keys` — create / copy-once / revoke
- Audit events on key create/revoke

**Plans:**
- [ ] 14-01: API keys (schema + middleware + UI) + Send API idempotency key

### Phase 15: Notify — List-Unsubscribe + Suppression List (v0.1.7)

**Goal:** Gmail/Yahoo-compliant unsubscribe + auto-skip bounced/unsubscribed recipients on future sends.
**Depends on:** Phase 14 (API keys — used for signed unsubscribe tokens)

**Scope:**
- Signed unsubscribe URL token (HMAC via vault, scopes org+user+category) — cookie-less endpoint
- `GET /v1/notify/unsubscribe?token=...` — preview page + POST variant per RFC 8058
- Email sender adds `List-Unsubscribe: <mailto:...>, <https://.../unsubscribe?token=...>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click`
- New `29_fct_notify_suppressions` (org_id, email, reason_code, created_at) — codes: hard_bounce, manual, complaint
- Bounce webhook inserts on hard bounce
- Email sender skips recipients in suppression list (marks delivery `status=unsubscribed`)
- `/notify/settings` — Suppressions section with list + manual add + delete

**Plans:**
- [ ] 15-01: Signed unsubscribe token + List-Unsubscribe headers + suppression table + sender skip + Suppressions UI

### Phase 16: Notify — Scheduled Sends + Quiet Hours + User Timezone (v0.1.7)

**Goal:** Defer sends until future time or outside recipient's quiet hours. Per-user timezone.
**Depends on:** Phase 11 (Notify), Phase 5 (Users — adds tz column)

**Scope:**
- Add `timezone` to iam users (EAV via `dim_attr_defs`)
- Add `scheduled_at` + `send_after_local` + `send_before_local` honored by sender polls (already have `scheduled_at` column; honor it)
- Preferences page: per-user quiet hours (start/end in their tz) stored in user preferences
- Send API accepts `send_at: ISO8601` or `delay_seconds: int`
- Worker / sender poll: `WHERE (scheduled_at IS NULL OR scheduled_at <= NOW()) AND within_quiet_hours_ok(...)`
- In-app deliveries bypass quiet hours (they don't disturb anyone)
- UI: timezone selector on account page, quiet hours sliders on preferences

**Plans:**
- [ ] 16-01: User timezone + quiet hours + scheduled send honored by sender polls

### Phase 17: Notify — Channel Fallback (v0.1.7)

**Goal:** "Try webpush, if not delivered in N minutes and not opened, send email." Durable at-least-once multi-channel delivery.
**Depends on:** Phase 11 (Notify)

**Scope:**
- Template adds `fallback_chain: [{channel_id, wait_seconds}]` (JSONB column on templates)
- Worker creates primary-channel delivery; new `fallback_pending` status means "waiting for window"
- Background task: at `created_at + wait_seconds`, if delivery not opened/clicked/delivered → create next channel in the chain
- UI: template editor exposes fallback chain
- `Send API` also honors per-send `fallback_chain`
- Metrics: fallback-triggered deliveries tagged in audit metadata

**Plans:**
- [ ] 17-01: fallback_chain column + watcher task + template UI + E2E

### Phase 18: Notify — Per-Template Analytics UI (v0.1.7)

**Goal:** Deliverability dashboard per template: sent, delivered, opened, clicked, bounced, failed — over time. Funnel view.
**Depends on:** Phase 11 (Notify)

**Scope:**
- `GET /v1/notify/templates/{id}/analytics?from=...&to=...` — aggregates from `evt_notify_delivery_events`
- Funnel endpoint: sent → delivered → opened → clicked
- UI: `/notify/templates/[id]` adds an Analytics tab alongside the body editor
- Charts: time series (sparkline) + rate cards
- Export CSV

**Plans:**
- [ ] 18-01: Analytics endpoint + template detail page analytics tab + CSV export

### Phase 19: Developer Documentation Pass (v0.1.7)

**Goal:** Anyone can build a real business app on this backend after reading the docs. Integration guide, full API reference, template authoring, deployment + DKIM/DMARC, worked examples.
**Depends on:** Phases 14–18

**Scope:**
- `03_docs/00_main/09_guides/notify-integration.md` — "From zero to your first notification" (10 min quickstart)
- `03_docs/00_main/09_guides/notify-template-authoring.md` — Jinja2 variables, per-channel bodies, preheader, fallback chain, testing
- `03_docs/00_main/09_guides/notify-deployment.md` — SMTP providers (SendGrid/Postmark/Mailgun), DKIM/DMARC/SPF setup, custom tracking domain
- `03_docs/00_main/09_guides/notify-api-reference.md` — Every endpoint with request/response examples + `curl` + TypeScript snippets
- `03_docs/00_main/09_guides/notify-examples/` — real business app recipes (password reset, order confirmation, weekly digest, admin alert broadcast)
- OpenAPI spec generation — `/openapi.json` exposed (FastAPI auto), linked from docs
- Postman collection / httpie requests file checked into `03_docs/00_main/09_guides/notify-examples/`
- README pointer updated

**Plans:**
- [ ] 19-01: Write all notify guides + generate OpenAPI spec + examples folder + README pointers

### Phase 20: IAM Hardening for OSS (v0.1.6)

**Goal:** Make IAM production-grade before open-sourcing. Every threshold/TTL/limit must live in vault-backed config (zero hardcoded values); email OTP must reuse existing Notify templates (no new mailer); audit coverage closed across all auth flows; account lockout, session limits, and password-reset session revocation wired in; TOTP backup codes + API key rotation + IAM metrics.
**Depends on:** Phase 7 (Vault — config storage), Phase 10 (Audit — emit_audit), Phase 11 (Notify — email templates), Phase 13 (Monitoring — metric emit).
**Status:** ✅ Complete (2026-04-17) — 137 tests passing, all 6 plans shipped.

**Scope decisions (confirmed 2026-04-17):**
- **Per-org policy**: global defaults + per-org override (1-B). Storage: vault paths only (no EAV). Global at `iam.policy.{key}`; per-org override at `iam.policy.orgs.{org_id}.{key}`. Resolver reads org-scoped key first, falls back to global.
- **Config granularity**: per-key (2-B). ~20 vault keys. Each change audited independently via existing vault audit path.
- **Admin UI**: split into own plan 20-02 (3-B-split). 20-01 is backend-only.
- **Hot-reload**: immediate invalidate on PATCH (4-B). `VaultClient.invalidate(key)` called in same tx as write, consistent with Phase 7 vault rotate/delete.

**Scope (must-fix from pre-OSS audit; deferred: passkey hardening, signin/signup rate limiting, HIBP, 2FA enforcement, session IP-binding):**
- **Policy config layer**: vault config keys (global at `iam.policy.{key}`; per-org override at `iam.policy.orgs.{org_id}.{key}`):
  - `password.min_length`, `password.require_upper`, `password.require_digit`, `password.require_symbol`, `password.min_unique_chars`
  - `lockout.threshold_failed_attempts`, `lockout.window_seconds`, `lockout.duration_seconds`
  - `session.max_concurrent_per_user`, `session.idle_timeout_seconds`, `session.absolute_ttl_seconds`, `session.eviction_policy` (oldest|lru|reject)
  - `magic_link.ttl_seconds`, `magic_link.rate_limit_per_email`, `magic_link.rate_window_seconds`
  - `otp.email_ttl_seconds`, `otp.email_max_attempts`, `otp.rate_limit_per_email`, `otp.rate_window_seconds`, `otp.totp_window`
  - `password_reset.ttl_seconds`
  - `AuthPolicy` service: `resolve(org_id, key) -> value`; SWR-cached via VaultClient (60s); immediate invalidate on PATCH
- **Account lockout**: `fct_failed_auth_attempts` table (user_id or email + source_ip + created_at) + service checks threshold within window on signin → sets `locked_until` via dtl_attrs → signin rejects until unlock
- **Session limits**: session service enforces `max_concurrent_per_user` at creation (evict oldest / LRU / reject per policy); middleware checks `idle_timeout_seconds` against `last_activity_at` (new column on fct_sessions) and `absolute_ttl_seconds` vs `created_at`; bumps `last_activity_at` on each authenticated request
- **Password reset session revocation**: `complete_reset` revokes all active sessions for the user atomically in the same tx as password update
- **Audit coverage closure**: emit on `iam.magic_link.consume_failed`, `iam.otp.email.verify_succeeded`, `iam.otp.email.verify_failed`, `iam.otp.totp.verify_succeeded`, `iam.otp.totp.verify_failed`, `iam.otp.totp.enrolled`, `iam.otp.totp.deleted`, `iam.password_reset.requested`, `iam.password_reset.completed`, `iam.credentials.verify_failed`, `iam.lockout.triggered`, `iam.lockout.cleared`
- **TOTP backup codes**: new `fct_totp_backup_codes` (user_id, argon2id hash, consumed_at); generated on TOTP enroll (10 codes, single-use); consume flow integrated into `/auth/otp/verify`
- **Email OTP → Notify migration**: refactor `12_otp/service.py` email send path to call `POST /v1/notify/send` with template key `iam.otp.email` (template created as part of this plan, uses existing transactional group); delete any inline SMTP/aiosmtplib call from 12_otp
- **API key rotation**: `POST /v1/api-keys/{id}/rotate` — atomically marks old revoked + issues new secret with same scopes; `last_used_at` column updated by Bearer middleware on each auth success
- **IAM metrics**: emit via existing `monitoring.metrics.increment` node — `iam_failed_auth_total{reason,source}`, `iam_lockouts_triggered_total`, `iam_sessions_evicted_total{reason}`, `iam_active_sessions` (gauge via periodic task), `iam_otp_verify_total{kind,outcome}`, `iam_password_reset_total{outcome}`

**Plans:**
- [ ] 20-01: Auth policy backend — vault key schema + `AuthPolicy` service (global + per-org resolver, SWR cache, immediate invalidate on PATCH) + safe-default bootstrap seed + pytest
- [ ] 20-02: Auth policy admin UI — `/iam/security/policy` page (global settings form + per-org override section) + Robot E2E
- [ ] 20-03: Account lockout (`fct_failed_auth_attempts` + lockout enforcement in credentials signin + audit emissions + `iam.lockout.*` events)
- [ ] 20-04: Session limits + idle timeout (`last_activity_at` column + concurrent-session eviction + idle/absolute TTL enforcement in SessionMiddleware + audit emissions)
- [ ] 20-05: Password reset session revocation + audit coverage closure across OTP/magic-link/password-reset (emit events + test coverage)
- [ ] 20-06: TOTP backup codes + Email OTP migration to Notify templates + API key rotation + `last_used_at` + IAM metrics (6 counters + 1 gauge)

### Phase 21: IAM OSS Completion (v0.1.6)

**Goal:** Close the OSS user-experience + compliance gaps that block a real v0.1.6 open-source release. Email verification at signup, admin invite flow, first-run admin wizard, user deactivation vs soft-delete distinction, GDPR export + erasure, end-user session/device management UI.
**Depends on:** Phase 11 (Notify — for verification/invite emails), Phase 20 (policy layer for signup.require_email_verification toggle).
**Status:** ✅ Complete (2026-04-17) — all 6 plans shipped, 137 IAM tests green.

**Scope:**
- **Email verification at signup**: new sub-feature `16_email_verification/`, `fct_email_verifications` table (user_id, hashed token, consumed_at, ttl_at), policy-gated (`signup.require_email_verification` in 20-01 vault config). Verification email uses Notify template `iam.email.verify`. Unverified users can sign in but get a banner + limited scope until verified.
- **Admin invite flow**: new sub-feature `17_invites/`, `fct_user_invites` table (email, org_id, role_ids, invited_by, expires_at, consumed_at, token_hash). `POST /v1/invites` creates + sends email (template `iam.invite.email`). `/auth/accept-invite?token=...` lands on a signup-with-prefilled-email flow that skips email verification (invite proves ownership). Invite policy keys in vault: `invite.ttl_seconds`, `invite.resend_cooldown_seconds`.
- **First-run admin wizard**: on boot, if `fct_users` has zero rows, backend enters "setup mode" — all routes except `POST /v1/setup/initial-admin` and `GET /v1/setup/status` return 503 with setup hint. First call creates the super-admin with TOTP mandatory + writes a `system_initialized` bootstrap flag in vault.configs. Frontend has `/setup` page that detects setup mode and renders an admin-creation form.
- **Deactivation vs soft-delete**: today `deleted_at` is the only off-state. Add `is_active BOOLEAN` via dtl_attrs (already registered or register in this plan): `deactivated = can_reactivate=true, preserves_all_data`; `deleted = deleted_at set, pseudonymized, sessions revoked, email hashed`. PATCH `/v1/users/{id}` with `{status: "inactive"}` deactivates; DELETE soft-deletes + pseudonymizes (replace email with `deleted-{uuid}@removed`, clear display_name).
- **GDPR export + erasure**: `POST /v1/account/data-export` creates an async job (evt_audit_outbox pattern) that assembles user's data from all features (orgs, workspaces, notifications, sessions, audit events where actor=user). Result emailed as signed download link (Notify template). `POST /v1/account/delete-me` performs pseudonymization flow — requires password confirmation + 2FA if enabled. 30-day recovery window before hard-erase purge job runs.
- **Session/device management UI**: `/account/sessions` shows every active session with {user-agent parsed via `user-agents` python lib, IP, created_at, last_activity_at, current-flag}. Per-row "Sign out this device" + "Sign out all other devices" buttons. Powered by existing 09_sessions API + 20-04 last_activity_at.
- **SECURITY.md + CODE_OF_CONDUCT.md + responsible disclosure contact** — OSS hygiene files at repo root.

**Plans:**
- [ ] 21-01: Email verification at signup (schema + service + routes + notify template + policy gate + frontend verify page + Robot E2E)
- [ ] 21-02: Admin invite flow (schema + service + routes + notify template + accept-invite page + Robot E2E)
- [ ] 21-03: First-run admin wizard (setup-mode gate + routes + /setup page + bootstrap flag + Robot E2E)
- [ ] 21-04: Deactivation vs soft-delete (is_active dtl_attr + PATCH status semantics + DELETE pseudonymization + frontend UI + tests)
- [ ] 21-05: GDPR export + erasure (async job + data assembler + signed download + delete-me flow + 30-day recovery + Robot E2E)
- [ ] 21-06: Session/device management UI + SECURITY.md + CODE_OF_CONDUCT.md (frontend page + OSS docs + Robot E2E)

### Phase 22: IAM Enterprise (v0.1.9)

**Goal:** Simple, elegant enterprise IAM with feature parity to Keycloak/Zitadel/Clerk/Okta on the 7 features customers actually use. Simplicity over completeness.
**Depends on:** Phase 20 (policy layer), Phase 21 (invite + email verification reused by JIT provisioning).
**Status:** 🚧 In Progress (v0.1.9 milestone)
**Testing:** pytest (backend) + Playwright MCP UI verification per plan. No Robot Framework.

**Scope:**
- **OIDC SSO**: `18_oidc_sso/` sub-feature. Per-org OIDC provider config (issuer, client_id, client_secret vault_key, scopes, claim mapping). OAuth2 authorization-code + PKCE. `/auth/oidc/{org_slug}/initiate` + `/auth/oidc/{org_slug}/callback`. JIT user create/update on callback. Uses `authlib`. Admin UI to configure per-org IdP.
- **SAML 2.0 SSO**: `19_saml_sso/` sub-feature. Per-org IdP config (entity_id, metadata_url_or_xml, cert, attribute mapping). SP metadata endpoint; ACS consumer → JIT user create/update + session. Uses `python3-saml`. Per-IdP keys in vault. Admin UI to configure per-org IdP.
- **SCIM 2.0 provisioning**: `20_scim/` sub-feature. Per-org SCIM bearer token. `/scim/v2/{org_slug}/Users` + `/Groups` per RFC 7644. {list, get, create, patch, delete}. Idempotent (409 on duplicate externalId). Deprovisioning → deactivate user + revoke sessions. Okta + Azure AD tested.
- **Admin impersonation**: `POST /v1/admin/impersonate/{user_id}` — super-admin only, MFA re-auth required. Session carries `impersonator_user_id`; every action emits dual-actor audit. Persistent red banner in UI. Auto-ends 30 min (configurable vault key). `POST /v1/admin/end-impersonation` to revert.
- **MFA enforcement policy**: Per-org + per-role policy key (`mfa.required = true/false`) read from existing AuthPolicy service (Phase 20). On signin, if policy requires MFA and user has no TOTP/passkey enrolled, redirect to enrollment before session is created. Admin UI toggle under `/iam/security/policy`.
- **IP allowlisting per org**: `fct_org_ip_allowlist` (org_id, cidr, label, created_by). Middleware checks session org → allowlist → reject if non-empty and IP doesn't match. Empty = unrestricted (default). Admin UI under `/iam/security/ip-allowlist`.
- **Audit SIEM export**: `21_siem_export/` sub-feature. Per-destination config (kind: `webhook` | `s3` | `splunk_hec`; credentials → vault). Worker tails `evt_audit_outbox`, formats, delivers. Retries + simple DLQ. Admin UI to configure destinations.

**Plans:**
- [ ] 22-01: OIDC SSO (authlib + PKCE + per-org config + JIT user + admin UI + Playwright MCP verify)
- [ ] 22-02: SAML 2.0 SSO (python3-saml + per-org IdP config + JIT user + admin UI + Playwright MCP verify)
- [ ] 22-03: SCIM 2.0 provisioning (RFC 7644 + bearer token + Okta/Azure + pytest)
- [ ] 22-04: Admin impersonation (dual-actor audit + red banner UI + 30-min timeout + Playwright MCP verify)
- [ ] 22-05: MFA enforcement policy (AuthPolicy gate on signin + enrollment redirect + admin UI toggle + pytest)
- [ ] 22-06: IP allowlisting per org (schema + middleware + admin UI + Playwright MCP verify)
- [ ] 22-07: Audit SIEM export (webhook/S3/Splunk destinations + outbox worker + admin UI + pytest)

### Phase 23: Feature Flag Engine Foundation (v0.2.0)

**Goal:** Working feature flag engine end-to-end — schema, evaluation, management API, basic admin UI. No SDK or gateway compilation yet.
**Depends on:** Phase 9 stub schema, Phase 22 (org/policy context), Phase 10 (audit emit)
**Reference:** `99_ref/backend/03_auth_manage/03_feature_flags/` — 4-table normalized schema, rule walker with priority, deterministic rollout hash

**Scope:**
- Feature `09_flags` + schema `"09_flags"` with tables: `fct_flags`, `fct_flag_states` (per-env), `fct_rules` (targeting, priority ordered), `fct_overrides` (force-value per entity)
- Dims: `environments` (dev/staging/prod), `value_types` (bool/string/number/json), `scopes` (global/org/application), `flag_permissions` (view/toggle/write/admin ranked)
- Evaluation engine: override → rule walk (priority ASC) → env default → global default
- Targeting JSON condition tree: `and/or/not/eq/neq/in/startswith/endswith/contains`
- Deterministic rollout: `hash(flag_key + entity_id) % 100 < rollout_percentage`
- `flags.flag.evaluate` control node (tx=caller, read-only) with SWR cache
- Mutation audit: `flags.flag.created|updated|deleted|activated|deactivated`, same for rules + overrides
- Basic admin UI at `/admin/flags` (list + create + edit, raw JSON for rules in this phase)
- Playwright MCP verify: create flag → add rule → evaluate → see value

**Plans:**
- [ ] 23-01: Schema + dim seeds + feature manifest entry + pytest smoke
- [ ] 23-02: Evaluation engine (rule walker + rollout hash + JSON condition evaluator + override precedence + scope resolution + SWR cache + `flags.flag.evaluate` node)
- [ ] 23-03: Management API (CRUD flags/rules/overrides) + mutation audit + basic admin UI + Playwright MCP verify

### Phase 24: Feature-Scoped Permissions + Role Redesign (v0.2.0)

**Goal:** Permissions move from hardcoded to manifest-declared. Roles restructured to carry `role_level + permissions + flag_grants`. `require_permission` wired site-wide. `AccessContext` primitive live.
**Depends on:** Phase 23 (flags must exist to bundle into roles), Phase 6 (existing role backend), Phase 10 (audit emit)
**Reference:** `99_ref/backend/03_auth_manage/04_roles/`, `_permission_check.py`, `06_access_context/`

**Scope:**
- `dim_permissions` table + feature manifest declaration block + boot seeder (idempotent upsert; manifest reload updates)
- Backfill: declare existing permissions in manifests for iam, audit, vault, notify, monitoring
- Role schema extension: `role_level` (platform/org/workspace), `scope_org_id`, `scope_workspace_id`, `is_system`
- `lnk_role_permissions` (role → permission) + `lnk_role_flag_grants` (role → flag + permission_level)
- `require_permission(user_id, perm_code, scope_org_id?, scope_workspace_id?)` helper — inline call pattern, raises `AuthorizationError`
- `AccessContext` resolver: per-request bundle `{user_id, org_id, ws_id, permissions: Set, flags: Map, views: Set}`, 5-min SWR cache keyed on `(user_id, org_id, ws_id)`, invalidate on role/assignment change
- Wire `require_permission` into all existing feature routes (iam, audit, vault, notify, monitoring)
- Audit `authz.permission.checked` behind `authz.audit_checks` policy flag (default off — perf)

**Plans:**
- [ ] 24-01: `dim_permissions` schema + manifest declaration + seeder + backfill all existing features + pytest
- [ ] 24-02: Role schema redesign (role_level, scope, flag_grants, permission_level) + migrate existing roles + role CRUD API updated + tests green
- [ ] 24-03: `require_permission` helper + `AccessContext` resolver + per-request dependency injection + wire into all existing routes + audit integration

### Phase 25: SDK + Gateway Compilation (v0.2.0)

**Goal:** External consumers can evaluate flags. Request-path flags compile to APISIX — gateway evaluates without backend hit.
**Depends on:** Phase 23 (evaluation engine), Phase 24 (permission checks protect SDK endpoints), APISIX

**Scope:**
- Python SDK: `tennetctl-sdk-py` — `Client.evaluate(flag_key, entity)`, `evaluate_bulk([...])`, 60s SWR cache
- TypeScript SDK: `@tennetctl/sdk` — zero-dep (native fetch), same API shape
- Evaluation endpoint: `POST /v1/flags/evaluate` + `POST /v1/flags/evaluate-bulk` (returns `{value, source, matched_rule_id?}`)
- Flag `kind` attribute: `effect` (backend-evaluated) or `request` (APISIX-compiled)
- APISIX sync worker: on `request`-kind flag mutation, push config to APISIX via Admin API (plugin = `traffic-split` for rollout, `consumer-restriction` for segment match)
- Audit every APISIX sync: `flags.apisix.synced|sync_failed`

**Plans:**
- [ ] 25-01: Python + TypeScript SDK thin clients + evaluation endpoints + SWR cache + SDK tests
- [ ] 25-02: APISIX compilation for request-path flags + sync worker + audit + live APISIX integration test

### Phase 26: Awesome UX — Flag Dashboard + Role Designer + Playground (v0.2.0)

**Goal:** Port the reference UX patterns verbatim. Three major pages: flag dashboard, role designer, evaluation playground + rule builder.
**Depends on:** Phases 23–25 (complete backend)
**Reference:** `99_ref/frontend/apps/web/src/app/(005_admin)/admin/feature-flags/` and `admin/roles/` (1,308 + 1,379 lines of Next.js patterns to port)

**Scope:**
- Flag Dashboard (`/admin/flags`): grouped list by category with collapse/expand; stat cards with colored left borders; inline environment status indicator (highest-reached); inline edit pickers for simple state changes; modal for full edit; permission presets (None/View/RW/Full/Admin); search + filter pills
- Role Designer (`/admin/roles`): grouped by role_level (Platform/Org/Workspace) with collapsible headers; expandable rows with 3 tabs (Permissions / Flag Grants / Audit); permission matrix (feature rows × action columns) with search; flag-grants picker with permission-level dropdown; scope-aware filtering pills; duplicate/disable/delete actions; smart code auto-generation
- Targeting Rule Builder: form-based tree editor (NOT freeform JSON) — guided add/edit of conditions with operator dropdowns + attr/value inputs; nested and/or/not groups; preview audience size
- Evaluation Playground (`/admin/flags/playground`): input `(flag_code, entity_id, attribute_context)`, see full resolution trace (which branch won? which rule matched? what was the hash bucket?)

**Plans:**
- [ ] 26-01: Flag Dashboard — list, stat cards, inline pickers, env status, permission presets, create/edit modals + Playwright MCP verify
- [ ] 26-02: Role Designer — grouped list, expandable rows, permission matrix, flag-grants picker, scope filter + Playwright MCP verify
- [ ] 26-03: Targeting Rule Builder + Evaluation Playground + Playwright MCP verify

### Phase 27: Portal Views + AuthZ Audit Explorer (v0.2.0)

**Goal:** Role-gated UI navigation (ref's `portal_views` concept) + focused audit view for authz events.
**Depends on:** Phases 24 (AccessContext), 26 (UX patterns), Phase 10 (audit explorer pattern)
**Reference:** `99_ref/backend/03_auth_manage/16_portal_views/`

**Scope:**
- `dim_portal_views` (code, name, icon, color, default_route) + `fct_view_routes` (per-view nested routes with sidebar metadata) + `lnk_role_views` (role → view)
- Resolver: `AccessContext.views` populated via same 4-path role walk
- Admin UI: define views + assign to roles
- Frontend navigation shell: reads resolved views from AccessContext, renders top-level menu accordingly; hides routes user can't access
- Seeded portals: `platform`, `iam`, `audit`, `monitoring`, `notify`, `vault`, `flags`
- AuthZ Audit Explorer (`/audit/authz`): pre-filtered to categories `authz.permission.checked`, `flags.evaluated`, `authz.access_context.resolved`, `roles.*`, `flags.*.mutated`
- Timeline + per-permission/per-flag aggregates + saved views

**Plans:**
- [ ] 27-01: Portal Views backend + admin UI + frontend navigation integration + Playwright MCP verify
- [ ] 27-02: AuthZ Audit Explorer (pre-filtered view + aggregates + saved views) + Playwright MCP verify

---

### Phase 28: SDK Core — skeleton + auth module (v0.2.1)

**Goal:** Both `tennetctl-py` (Python) and `@tennetctl/sdk` (TypeScript) exist with a working transport layer and a complete `auth` module.
**Depends on:** 23R (unified role/permission model), Phase 14 (API key middleware).

**Scope:**
- Package scaffolding: `sdk/python/` + `sdk/typescript/` in repo, versioning (semver), release pipeline (PyPI-ready + npm-ready; internal registry for v1)
- Transport layer: `httpx.AsyncClient` (py) + native `fetch` (ts); bearer auth from API key or session cookie; retry with exponential backoff; envelope parsing (`{ok, data, error}`)
- `client.auth` module parity across both languages:
  - `signin(email, password)` / `signin_with_oauth(provider)`
  - `signout()`
  - `me()` → session user
  - `session.validate(token)` / `session.list()` / `session.revoke(id)`
  - `api_keys.list()` / `api_keys.create(name, scopes)` → `{token_shown_once, ...}` / `api_keys.revoke(id)` / `api_keys.rotate(id)`
- Typed errors: `TennetctlError` base + `AuthError`, `RateLimitError`, `NetworkError` subclasses
- pytest + vitest coverage ≥80% on transport + auth
- SDK quickstart guide in `03_docs/00_main/09_guides/sdk-quickstart.md`

**Plans:**
- [x] 28-01: Python SDK — scaffolding + transport + `client.auth` + pytest (2026-04-18)
- [x] 28-02: TypeScript SDK — scaffolding + transport + `client.auth` + vitest (2026-04-18)

### Phase 29: SDK Core — flags + iam + audit + notify modules (v0.2.1) — ✅ COMPLETE 2026-04-18

**Goal:** SDK covers the "core business workflow" set — feature flags, IAM read helpers, audit query, transactional notify.

**Shipped:**
- `client.flags.evaluate(key, entity, context?)` + `evaluate_bulk` with 60s TTL cache (Python + TS)
- `client.iam.users/orgs/workspaces/roles/groups.list/get` read-only (Python + TS)
- `client.audit.events.list/get/stats/tail/funnel/retention/outbox_cursor/event_keys` — NO emit() (backend-only via node)
- `client.notify.send(template_key, recipient_user_id, variables?, channel?, idempotency_key?)` — optional `Idempotency-Key` header
- 26 new Python tests + 21 new TS tests = 47 new tests in this phase
- Per-module reference docs updated

**Plans:**
- [x] 29-01: Python flags/iam/audit/notify + pytest (2026-04-18)
- [x] 29-02: TypeScript flags/iam/audit/notify + vitest (2026-04-18)

---

### Phase 30: SDK Observability — metrics + logs (v0.2.2)

**Goal:** `client.metrics` and `client.logs` modules with async batching, cardinality caps, and fail-open semantics.
**Depends on:** Phase 29 (SDK core complete), Phase 13-02 (metrics backend), Phase 13-03 (logs backend)

**Scope:**
- `client.metrics.increment(name, value?, labels?)`, `.observe(name, value, labels?)`, `.gauge_set(name, value, labels?)`
- `client.logs.emit(level, msg, attrs?)` — structlog-compatible in py; console-bridge available in ts
- Async batch flush (configurable window, default 1s / 100 items); drops after retry budget, never blocks
- Cardinality cap enforced SDK-side (mirrors backend's `MetricsStore.increment` behavior)
- Sampling policy exposed as config

**Plans:**
- [ ] TBD during /paul:plan

### Phase 31: SDK Observability — traces + auto-instrument (v0.2.2)

**Goal:** Distributed tracing in the SDK + one-line auto-instrument for Python backend services. Browser SDK captures page-view + long-task traces.
**Depends on:** Phase 30 (logs/metrics infrastructure), Phase 13-03 (OTLP receiver)

**Scope:**
- `client.traces.start_span(name, parent_ctx?)` with context managers (py) / async-local-storage (ts)
- W3C trace-context propagation — inject/extract HTTP headers
- `tennetctl.autoinstrument(app)` — one call instruments FastAPI + asyncpg + httpx + Jinja2 in Python
- Browser SDK: auto page-view, long-task, first-input-delay, cumulative-layout-shift captured as spans
- Sampling policy: head-based (fixed %) + tail-based (keep all errors + slow)

**Plans:**
- [ ] TBD during /paul:plan

---

### Phase 32: SDK Platform — vault + catalog modules (v0.2.3)

**Goal:** Close SDK coverage — vault secret access (scoped, audited, never cached in SDK memory) + catalog inspection (useful for meta-UIs and for the v0.4.0 canvas).
**Depends on:** Phase 29 (SDK core), Phase 7 (vault backend), Phase 2 (catalog).

**Scope:**
- `client.vault.get_secret(key)` — forwards to `/v1/vault/{key}`; server-side audit; SDK never caches plaintext
- Browser TS SDK: `vault.get_signed_ref(key)` — returns short-lived HMAC URL, never plaintext in browser memory
- `client.catalog.list_features()`, `.list_sub_features(feature?)`, `.list_nodes(feature?, kind?)`, `.get_flow(key)` — read-only manifest inspection
- Full OpenAPI spec + SDK regeneration CI check (drift → fail build)

**Plans:**
- [ ] TBD during /paul:plan

### Phase 33: APISIX Gateway Sync (v0.2.3)

**Goal:** Request-path flags evaluate at the gateway with zero backend round-trip.
**Depends on:** 23R (flag engine), running APISIX container.

**Scope:**
- Add `kind` column on `fct_flags` (dim: `effect` / `request`)
- APISIX sync worker: on `request`-kind flag mutation, PATCH APISIX Admin API with `traffic-split` (rollout %) + `consumer-restriction` (segment match)
- Boot reconcile: on startup, diff APISIX state vs Postgres `request`-kind flags, push deltas
- Audit `flags.apisix.synced` / `flags.apisix.sync_failed` with payload diff
- Admin UI badge on each flag showing APISIX sync status (in-sync / drift / sync-failed)
- Live integration test: mutate flag → observe APISIX config change → curl through gateway sees new value

**Plans:**
- [ ] TBD during /paul:plan

---

### Phase 34: Admin UI — coverage audit (v0.2.4)

**Goal:** Produce a coverage matrix: every feature module × every admin surface it needs × current status. Output drives Phases 35–36.
**Depends on:** 23R (unified role/permission model), Phase 29 (SDK available for dogfooding).

**Scope:**
- Walk every feature in `backend/02_features/` and every sub-feature
- For each sub-feature, enumerate expected admin pages (list, detail, create/edit, settings)
- Check which exist in `frontend/src/app/` and which are stub/missing
- Severity ranking: critical (blocks admin day-to-day) / nice-to-have / polish
- Output: `.paul/phases/34-admin-ui-coverage-audit/COVERAGE-MATRIX.md`
- Known gaps to verify: Workspaces UI, Catalog browser, System health dashboard, Module toggles, Auth policy at-scale, Notify Suppressions + Scheduled + Fallback + Analytics depth, SIEM destinations, Portal Views (from 23R), AuthZ Explorer (from 23R)

**Plans:**
- [ ] TBD during /paul:plan

### Phase 35: Admin UI — build missing critical pages (v0.2.4)

**Goal:** Close all critical-severity gaps from the Phase 34 coverage matrix. Every page dogfoods the unified SDK.
**Depends on:** Phase 34 (coverage matrix), Phase 29 (SDK).

**Scope:**
- Build pages enumerated as critical in Phase 34 output
- All frontend code uses `@tennetctl/sdk` — zero direct `apiFetch` calls in new code
- Design tokens + component library: standardize table, filter, action button, loading/empty/error states
- Permission-gate every page via resolved role (23R unified model)
- Playwright MCP verification per page

**Plans:**
- [ ] TBD during /paul:plan

### Phase 36: Admin UI — polish + unified nav (v0.2.4)

**Goal:** Every admin surface feels like one product. Portal views (deferred from 23R) drive role-gated navigation.
**Depends on:** Phase 35 (pages exist).

**Scope:**
- Port the original 23R Phase 27 portal-views model: `dim_portal_views` + `fct_view_routes` + `lnk_role_views`
- Frontend navigation shell reads resolved views from AccessContext, renders per-role sidebar, hides routes user can't access
- Seeded portals: `platform`, `iam`, `audit`, `monitoring`, `notify`, `vault`, `flags`, `catalog`
- AuthZ Audit Explorer (`/audit/authz`) — pre-filtered view for authz events (also from 23R)
- Polish pass: loading skeletons consistent, empty states have actionable CTA, error boundaries recover gracefully

**Plans:**
- [ ] TBD during /paul:plan

---

### Phase 37: DX + Catalog Hot-Reload (v0.1.8)

**Goal:** Dev feedback loop under 5 seconds. Manifest change → catalog reloaded without restart.

**Scope:**
- `watchdog` on `feature.manifest.yaml` in dev mode (`TENNETCTL_ENV=dev` only)
- Re-run catalog upsert + cross-import linter on change
- Handler class caching in runner — eliminate per-invocation `import_module`
- Pre-commit hook wires cross-import linter; documented in CONTRIBUTING

**Plans:**
- [ ] TBD during /paul:plan

### Phase 38: Auth Hardening — rate limit, HIBP, passkey, 2FA policy (v0.1.8)

**Goal:** Close pre-OSS audit gaps deferred from v0.1.6.

**Scope:**
- Signin/signup rate limiting per-IP + per-email (Valkey counters; Postgres fallback)
- HaveIBeenPwned k-anonymity check on password create/update; blocks if breached
- Passkey hardening — full `iam.passkey.*` audit, device revocation, attestation verification
- 2FA-required policy enforcement — per-org + per-role gate blocks session creation if unenrolled

**Plans:**
- [ ] TBD during /paul:plan

### Phase 39: NCP v1 Maturity — doc sync, versioning, bulk ops (v0.1.8)

**Goal:** Protocol doc matches reality; versioning pattern demonstrated; bulk ops documented.

**Scope:**
- NCP v1 §9 doc sync (setup-bypass + authz hook)
- NCP v1 §11 doc sync (control nodes may read)
- `get_many` alongside every `get` in repos + services; CONTRIBUTING updated
- v1 → v2 node migration demonstrated on one real upgrade
- `pool` promoted from `NodeContext.extras['pool']` to first-class field

**Plans:**
- [ ] TBD during /paul:plan

---

### Phase 40: Monitoring Alerting (v0.3.0)

**Goal:** Unpause Phase 13-08. Ship alert rules + evaluator + silences + Notify integration end-to-end.
**Depends on:** Phase 13 (paused at 13-07), Phase 11 (Notify critical category).

**Scope:**
- Alert rule designer UI (metric + threshold + duration + channels)
- Alert evaluator worker; LISTEN/NOTIFY sub-minute evaluation
- Silences with expiration + dedup window + escalation chain
- Deliver via Notify `critical` category
- Alerts UI: active / acked / silenced / history
- pg_cron partition manager verified in live deploy; retention tiers working

**Plans:**
- [ ] TBD during /paul:plan

### Phase 41: Monitoring SLO + dashboard sharing (v0.3.0)

**Goal:** SLO tracking + dashboard sharing + saved queries. (Monitoring SDK already lives in v0.2.2.)

**Scope:**
- SLO tracking: error-budget calc on top of metrics; burn-rate rendering
- Saved queries + per-user query history
- Signed dashboard share links (optional embed token)

**Plans:**
- [ ] TBD during /paul:plan

---

### Phase 42: Flow schema + backend (v0.4.0)

**Goal:** Activate flow composition tables the catalog has referenced but never populated.

**Scope:**
- `fct_flows`, `fct_flow_nodes`, `lnk_flow_edges` migrations
- Manifest-driven flow registration (feature declares flows alongside nodes)
- DAG acyclicity + typed-edge compatibility validation
- Read-path endpoints exposed via `client.catalog.get_flow(key)` (from Phase 32)

**Plans:**
- [ ] TBD during /paul:plan

### Phase 43: Canvas renderer (v0.4.0)

**Goal:** React Flow reads live catalog and renders every flow as a DAG. Canvas consumes the same `client.catalog` external apps use.

**Scope:**
- `/flows` list + `/flows/[key]` detail using React Flow (XY Flow)
- Typed ports per node (input/output schemas from manifest)
- Node detail drawer — schemas, handler path, execution policy
- Virtualization spike for >200-node flows

**Plans:**
- [ ] TBD during /paul:plan

### Phase 44: Trace overlay + search (v0.4.0)

**Goal:** Pick a trace_id; canvas animates node activation with timing. Searchable across flows.

**Scope:**
- Trace overlay — select trace_id, nodes animate in execution order with duration chips
- Search: find flows by node/feature/kind
- Recent-executions list on node detail drawer
- Permalink per flow (URL restores canvas state)

**Plans:**
- [ ] TBD during /paul:plan

---

## Future Milestones (post-v0.4.0)

### v0.2 Platform Access Layer
- **MCP Integration** — `inspect / search / scaffold / validate / run` generic tools (ADR-024) over the catalog
- Scaffolder CLI — template-driven feature/sub-feature/node creation
- Agent indices — `_index.yaml` generated alongside manifests if the simple pattern proves insufficient

### v1.0 Enterprise
- Multi-region catalog replication
- Visual flow editor (writeable canvas)
- Enterprise support contract tier

---
*Roadmap created: 2026-04-12*
*Last updated: 2026-04-18 — Rescoped around unified SDK + admin UI coverage. v0.2.0 closed via 23R. v0.2.1 Unified SDK Core active; v0.2.2/v0.2.3/v0.2.4 extend SDK + admin UI; v0.1.8/v0.3.0/v0.4.0 follow. Phases 28–44.*
