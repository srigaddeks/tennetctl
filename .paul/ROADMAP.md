# Roadmap: TennetCTL

## Overview

TennetCTL is built milestone-by-milestone from core infrastructure through enterprise IAM. Every phase after foundation is a full vertical slice: schema → repo → service → routes → nodes → UI → Playwright live verification. Nothing ships without being tested in a real browser.

**Architectural spine:** Node Catalog Protocol v1 (see `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`). Every feature vertical (Phase 3+) uses it.

## Current Milestone

**v0.1 Foundation + IAM** (v0.1.0)
Status: In progress
Phases: 7 of 12 complete — Phase 8 (Auth basics) in progress

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
| 12 | IAM Security Completion — Magic Link, OTP, Passkeys (vertical) | 4 | Not started | - |

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
**Status:** Not started

**Scope:**
- `sub_features/11_magic_link/` — signed single-use tokens (HMAC via vault), 10-min TTL, consumed-on-use, rate-limited by email + IP
- `sub_features/12_otp/` — email OTP (6-digit code, 5-min TTL) + TOTP (authenticator app, RFC 6238, `pyotp`). Recovery codes generated + stored hashed
- `sub_features/13_passkeys/` — WebAuthn passkeys via `webauthn-python`, multiple credentials per user, device naming, last-used tracking
- `sub_features/14_password_reset/` — email reset link, token same pattern as magic link, invalidates all sessions on reset
- `sub_features/15_account_recovery/` — email-based account recovery with admin approval escalation for locked-out org admins
- All flows emit audit events at every step (request/consume/fail); `critical` category for: repeated failed OTP, new-device passkey registration, password reset completion, account recovery initiation
- Account setup UI: per-user security page listing enrolled methods + add/remove flows
- Signin UI expansion: method picker (password / magic-link / OTP / passkey), graceful fallback if user has multiple methods
- Robot E2E: magic-link happy path (request → receive email via notify → click → signed in); OTP happy path; passkey registration + signin; password reset

**Plans:**
- [ ] 12-01: Magic link sub-feature + integration with Notify transactional send
- [ ] 12-02: OTP (email + TOTP) sub-feature + recovery codes
- [ ] 12-03: WebAuthn passkeys sub-feature
- [ ] 12-04: Password reset + account recovery flows + security UI + Robot E2E

---

## Future Milestones (post-v0.1)

### v0.1.5 Runtime Hardening (before v0.2)
Gaps surfaced during gap analysis (2026-04-16). Close before wider adoption:
- Versioning operationalized (v1 → v2 migration pattern working in practice)
- Async effect dispatch via NATS JetStream wired to effect nodes
- Gateway sync: request-kind nodes propagated to APISIX config
- Dev hot-reload of catalog on manifest change (not just restart)
- Bulk operation patterns documented (`get_many` alongside every `get`)

### v0.2 Platform Access Layer
- **MCP Integration** — `inspect / search / scaffold / validate / run` generic tools (ADR-024) over the catalog
- Scaffolder CLI — template-driven feature/sub-feature/node creation
- Agent indices — `_index.yaml` generated alongside manifests if the simple pattern proves insufficient
- Flow composition tables (`fct_flows`, `fct_flow_nodes`, `lnk_flow_edges`) activated — required before visual canvas

### v0.3 Canvas + Monitoring
- React Flow read-only canvas reads catalog + flows, renders DAG
- Monitoring feature vertical (traces, metrics, logs via NATS)

### v1.0 Enterprise
- Feature flag evaluation at gateway
- Multi-region catalog replication
- Visual flow editor (writeable canvas)

---
*Roadmap created: 2026-04-12*
*Last updated: 2026-04-16 — Added Phase 10 (Audit Analytics, PostHog-class) + Phase 11 (Notify, Mailchimp-class, 12 plans incl. template groups, SMTP-per-group, static+dynamic SQL variables, designer UI, pure API) + Phase 12 (IAM Security Completion: magic link, OTP, passkeys — depends on Notify)*
