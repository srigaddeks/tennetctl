# Roadmap: TennetCTL

## Overview

TennetCTL is built milestone-by-milestone from core infrastructure through enterprise IAM. Every phase after foundation is a full vertical slice: schema → repo → service → routes → nodes → UI → Playwright live verification. Nothing ships without being tested in a real browser.

**Architectural spine:** Node Catalog Protocol v1 (see `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`). Every feature vertical (Phase 3+) uses it.

## Current Milestone

**v0.1.9 IAM Enterprise** (v0.1.9)
Status: 🚧 In Progress
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
| 22 | IAM Enterprise — OIDC SSO, SAML SSO, SCIM, impersonation, MFA enforcement, IP allowlist, SIEM export (v0.1.9) | 7 | 🚧 In Progress | - |

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

---

## Future Milestones (post-v0.1.6)

### v0.1.8 Runtime Hardening (deferred gaps)
Gaps surfaced during gap analysis (2026-04-16). Close before wider adoption:
- Versioning operationalized (v1 → v2 migration pattern working in practice)
- Async effect dispatch via NATS JetStream wired to effect nodes
- Gateway sync: request-kind nodes propagated to APISIX config
- Dev hot-reload of catalog on manifest change (not just restart)
- Bulk operation patterns documented (`get_many` alongside every `get`)
- Passkey audit-coverage + hardening
- Signin/signup rate limiting (per-IP + per-email)
- HaveIBeenPwned breach-password check
- 2FA-required policy enforcement (per-org + per-role)

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
*Last updated: 2026-04-17 — v0.1.9 IAM Enterprise milestone opened. Phase 22 (8 plans) active. Testing convention changed: Robot Framework removed, Playwright MCP for UI verification going forward.*
