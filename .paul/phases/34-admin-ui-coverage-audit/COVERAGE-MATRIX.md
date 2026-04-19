# Admin UI Coverage Matrix

**Generated:** 2026-04-18 (Phase 34 audit)
**Scope:** Every backend feature/sub-feature × every expected admin surface × current status

**Severity scale:**
- 🔴 **Critical** — blocks day-to-day admin work
- 🟡 **Important** — frequent-use gap
- 🟢 **Nice-to-have** — polish / low frequency

## Legend

- ✅ shipped + working
- 🔧 shipped but thin (list-only, missing detail/create/edit paths)
- ❌ missing
- ⚠ exists but needs verification in browser

---

## Feature 03 — IAM (core, always-on)

| Sub-feature | Expected admin | Status | Severity if missing |
|---|---|---|---|
| orgs | list, detail, create, edit | 🔧 `/iam/orgs` — needs detail audit | 🟡 |
| workspaces | list, detail, create, edit, org-scope | ❌ no `/iam/workspaces/[id]` detail | 🔴 (backend shipped, UI gap blocks admin) |
| users | list, detail (with sessions, orgs, roles) | ✅ `/iam/users` + `/iam/users/[id]` | — |
| roles | list, Role Designer grid, detail | ✅ via 23R Role Designer | — |
| groups | list, detail, membership | 🔧 `/iam/groups` | 🟡 |
| applications | list, detail, scope assignment | 🔧 `/iam/applications` | 🟡 |
| invites | list, create | ✅ `/iam/invites` | — |
| memberships | list by user / org / workspace | 🔧 `/iam/memberships` | 🟡 |
| auth policy (20-02) | global + per-org override | ✅ `/iam/security/policy` | — |
| MFA enforcement (22-05) | toggle + enrollment status | ✅ `/iam/security/mfa` | — |
| IP allowlist (22-06) | CIDR list editor | ✅ `/iam/security/ip-allowlist` | — |
| OIDC SSO (22-01) | per-org IdP config | ✅ `/iam/security/sso` | — |
| SAML SSO (22-02) | per-org IdP config | ✅ `/iam/security/saml` | — |
| SCIM (22-03) | per-org bearer + status | ✅ `/iam/security/scim` | — |
| SIEM export (22-07) | destination config | ✅ `/iam/security/siem` | — |
| Portal views (23R follow) | view → route → role assignment | ⚠ `/iam/security/portal-views` exists — needs audit | 🟡 |
| Impersonation (22-04) | history + end-impersonation UI | ❌ no dedicated page | 🟡 |
| Setup wizard (21-03) | first-run admin creation | ✅ `/setup` | — |
| Email verification (21-01) | verify page + banner | ✅ `/auth/verify-email` | — |
| TOS / consent | accept screen | ⚠ `/iam/security/tos` exists — needs audit | 🟢 |

## Feature 02 — Vault

| Sub-feature | Expected admin | Status | Severity |
|---|---|---|---|
| secrets | list, create (with reveal-once), rotate, delete | ✅ `/vault/secrets` | — |
| configs | list, create, edit, delete | ⚠ `/vault/configs` exists — needs audit for per-org override visibility | 🟡 |

## Feature 04 — Audit

| Sub-feature | Expected admin | Status | Severity |
|---|---|---|---|
| events (query + explorer) | list, detail, filters, live tail | ⚠ `/audit` exists — needs depth audit | 🟡 |
| funnel | funnel builder | ❌ not visible | 🟡 |
| retention | retention curve | ❌ not visible | 🟢 |
| saved views | create/list/delete | ❌ not visible | 🟡 |
| authz explorer (31) | pre-filtered authz events | ✅ `/audit/authz` | — |

## Feature 05 — Monitoring

| Sub-feature | Expected admin | Status | Severity |
|---|---|---|---|
| metrics | registry list, dashboards | ⚠ `/monitoring/metrics` exists — depth unknown | 🟡 |
| logs | explorer + live tail | ⚠ `/monitoring/logs` exists | 🟡 |
| traces | list, trace detail (waterfall) | ⚠ `/monitoring/traces` + `/monitoring/traces/[traceId]` exist | 🟡 |
| dashboards | list, detail, CRUD | ⚠ `/monitoring/dashboards` + `/monitoring/dashboards/[id]` | 🟡 |
| alerts — rules | list, create, detail | ✅ `/monitoring/alerts/rules/*` | — |
| alerts — active | list, detail | ✅ `/monitoring/alerts` + `/monitoring/alerts/[id]` | — |
| alerts — silences | list + create | ✅ `/monitoring/alerts/silences` | — |
| saved queries | list + run | ❌ no dedicated page | 🟡 |
| synthetic checks | config + results | ❌ no page | 🟡 |

## Feature 06 — Notify

| Sub-feature | Expected admin | Status | Severity |
|---|---|---|---|
| templates | list, detail, editor, analytics | ⚠ `/notify/templates` + `/notify/templates/[id]` | 🟡 |
| template groups | list + edit SMTP binding | ❌ no admin page | 🟡 |
| smtp configs | list + edit (vault-linked) | ❌ no admin page | 🟡 |
| variables | list + editor | ❌ no admin page | 🟡 |
| deliveries | list + filters + retry | ⚠ `/notify/deliveries` | 🟡 |
| subscriptions | audit-event → template mapping | ❌ no admin page | 🔴 (subscribe to critical signals without UI is painful) |
| campaigns | list + builder + scheduler | ❌ no admin page | 🟡 |
| preferences | user-facing opt-out | ✅ `/notify/preferences` | — |
| suppressions | list + manual add | ❌ `/notify/settings` likely covers? — needs audit | 🟡 |
| analytics | per-template deliverability | ❌ not visible as separate page | 🟡 |
| send (transactional) | test-send form | ⚠ `/notify/send` — needs audit | 🟢 |
| webpush subscribe | service worker enroll | ⚠ in preferences | 🟢 |

## Feature 07 — Billing

❌ Feature not shipped yet. No admin surface expected.

## Feature 09 — Feature flags

| Sub-feature | Expected admin | Status | Severity |
|---|---|---|---|
| flag dashboard | list, stat cards, grouped, presets | ✅ `/feature-flags` (shipped via 23R) | — |
| flag detail | state per-env, rules, overrides | ✅ `/feature-flags/[flagId]` | — |
| evaluation playground | trace resolution | ⚠ `/feature-flags/evaluate` exists — needs audit | 🟡 |
| targeting rule builder | form-based tree editor | ❌ (part of detail page? needs audit) | 🟡 |

## Cross-cutting — Catalog

| Surface | Expected | Status | Severity |
|---|---|---|---|
| Nodes browser | list every registered node + schemas | ⚠ `/nodes` exists — depth unknown | 🟡 |
| Flows canvas | visual flow viewer | ❌ (v0.4.0 Phase 42–44) | — (out of scope for v0.2.4) |
| Features + sub-features list | platform-level inventory | ❌ | 🟡 |

## Cross-cutting — System

| Surface | Expected | Status | Severity |
|---|---|---|---|
| System health | module status, pool depth, NATS status | ❌ | 🔴 (no single pane of glass) |
| Module toggle inspector | which `TENNETCTL_MODULES` are enabled | ❌ | 🟡 (env-only today) |
| Background worker status | active workers, lag, last-run | ❌ | 🟡 |
| Migration history | `_migrations` table browser | ❌ | 🟢 |

## Account surfaces (end-user)

| Surface | Status |
|---|---|
| `/account/api-keys` | ✅ |
| `/account/security` (TOTP, passkeys) | ✅ |
| `/account/sessions` | ✅ |
| `/account/privacy` (GDPR export/erasure) | ✅ |

---

## Summary — Critical gaps (🔴)

1. **IAM Workspaces detail page** — backend shipped since Phase 4-02, admin has no detail/edit UI for a workspace
2. **Notify Subscriptions admin** — no UI to manage audit-event → template subscription mapping (core notify primitive)
3. **System Health dashboard** — no single place to see module status, worker lag, connection pool depth

## Summary — Important gaps (🟡)

- IAM Groups / Applications / Memberships thin (list only)
- Notify Template Groups / SMTP Configs / Variables / Suppressions admin pages missing
- Notify Campaigns admin missing
- Audit Funnel / Retention / Saved Views
- Monitoring Saved Queries / Synthetic Checks
- Catalog features/sub-features browser
- Impersonation history UI
- Module toggle inspector
- Portal Views depth audit

## Summary — Verification needed (⚠)

- `/iam/security/portal-views`, `/iam/security/tos`, `/vault/configs`, `/audit`, `/monitoring/*` (metrics/logs/traces/dashboards), `/notify/templates*`, `/notify/deliveries`, `/notify/settings`, `/notify/send`, `/feature-flags/evaluate`, `/nodes`

## Phase 35 scope proposal (build critical gaps)

Ordered by blast radius:
1. **35-01** Workspaces detail + edit + member list page
2. **35-02** Notify Subscriptions admin + Template Groups / SMTP Configs / Variables CRUD pages
3. **35-03** System Health page — aggregates module status, pool depth, NATS status, worker lag

## Phase 36 scope proposal (polish + nav)

1. **36-01** Unified sidebar via Portal Views (deferred from 23R-27)
2. **36-02** Standardize loading / empty / error states across all admin pages
3. **36-03** Replace direct `apiFetch` calls in frontend code with `@tennetctl/sdk` client usage
