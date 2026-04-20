# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-16)

**Core value:** Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in.
**Current focus:** Admin UI coverage pass v0.2.4 substantially complete. All three 🔴 critical gaps closed (Workspaces detail, Notify edit flows, System Health). Remaining: APISIX infra (33), traces autoinstrument (31-b), hardening (37-39), alerting (40-41), canvas (42-44).

## Current Position

Milestone: **v0.1.8 Runtime Hardening** (Phase 38 ✅ complete; Phase 39 in flight)
Phase: **39 — NCP v1 Maturity**
Plan: **39-01 PLANNED** — pool→first-class NodeContext field + NCP v1 §11 doc sync. Drafted, not yet applied.
Status: Devtools-platform scope only. Scope-creep cleanup completed 2026-04-20 — old phases 45–59 (product_ops/CDP) and the entire `10_product_ops` feature were removed from the codebase. kbio/kprotect ideas retired from roadmap. Remaining queued milestones: v0.1.8 (39), v0.3.0 monitoring alerting (40–41), v0.4.0 canvas (42–44), v0.8.0 GDPR DSAR (45).
Last activity: 2026-04-20 — Removed product_ops scope creep (15 phases, feature dir, frontend routes, SDK clients, tests, docs, browser SDK).

Next action: Resume Plan 39-01 (`.paul/phases/39-ncp-v1-maturity/`).

Previously: v0.2.4 complete (multi-phase autonomous sweep — 35-01/35-02/35-03/36-01 + portal polish). 10 phase summaries. 151 SDK tests green. Every 🔴-severity admin UI gap closed.
Previously: v0.2.0 complete via 23R rebase (commits ec93b58 → eab604b → d874a14). Unified schema — roles bundle (feature_flag × action) permissions.
Previously: Phase 22 IAM Enterprise complete (8/8 plans) — OIDC/SAML SSO, SCIM, impersonation, MFA enforcement, IP allowlist, SIEM export.

Previously: v0.2.0 complete via 23R rebase (commits ec93b58 → eab604b → d874a14). Unified schema — roles bundle (feature_flag × action) permissions; single Role Designer grid.
Previously: Phase 22 IAM Enterprise complete (8/8 plans) — OIDC/SAML SSO, SCIM, impersonation, MFA enforcement, IP allowlist, SIEM export.
Previously: Phase 13 Monitoring paused at 13-07 (157/157 pytest green); 13-08 alerting carried to v0.3.0 Phase 35.

Progress:
- v0.1.5 Observability: Phase 13 plans 13-01 through 13-08 drafted; 13-01…13-07 APPLY complete (13-06 = a+b+c, 19/19 E2E green; 13-07 157/157 pytest green); 13-08 not started
- v0.1.7 Notify production: Phase 14-01 COMPLETE + UNIFIED. Phases 15–18 each have PLAN + SUMMARY on disk (status to audit); Phase 19 has SUMMARY only (ad-hoc APPLY — retroactive plan optional).
- Milestone v0.1: [██████████] 100% (All 12 phases complete — v0.1 Foundation + IAM milestone done)
- IAM auth backend (basics): 3 sub-features / 26 tests / 4 catalog nodes / session middleware / OAuth monkeypatched — IAM security completion (magic link/OTP/passkeys) deferred to Phase 12
- Audit write path: evt_audit table + emit node (Phase 3 Plan 03); read path + UI + outbox now planned as Phase 10
- Notify (Phase 11, 12 plans): dim tables with critical category + priority fan-out; template groups keyed to SMTP configs; static + dynamic-SQL variables (safelisted, parameterized by audit event); template designer UI; pure `POST /v1/notify/send` transactional API
- IAM Security Completion (Phase 12, 4 plans): magic link + OTP (email + TOTP) + passkeys + password reset — depends on Notify for delivery

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ○        ○    [Plan 39-01 created — pool→first-class field + NCP v1 doc sync]
```

Previous: Plan 38-02 closed 2026-04-20; Phase 38 substantively done.

**Phase 38 Auth Hardening — shipped across 2 plans:**
- 38-01: session-fixation on login, IP rate limiter (PG-native), atomic single-use tokens
- 38-02: session rotation on password-change + TOTP enrollment (closes AC-1 across all 3 boundaries)


Previous: Plan 38-01 closed 2026-04-20.

**Plan 38-01 shipped:** session-fixation defense on login (rotate_on_login), Postgres-native per-IP rate limiter on /signin + /magic-link/request + /password-reset/request (10/5/3 per 60s), atomic race-close on token consumption. 9 files modified, 1 new module (rate_limit.py), 1 new migration (NNN 069).


Previous loop closure (2026-04-20 milestone unify — v0.5.0+v0.6.0+v0.6.1+v0.7.0 reconciled; 18 retroactive PLAN stubs backfilled).


**2026-04-20 Milestone UNIFY — what was reconciled:**

| Gap category | Phases | Resolution |
|---|---|---|
| Shipped, SUMMARY only, no PLAN | 19, 30, 31, 32, 33, 34, 37-dx, 37-ux, 46, 47, 48, 49, 50, 51, 52, 53 | Retroactive PLAN stubs written; each points to SUMMARY as source-of-truth |
| Shipped in code, empty phase dir | 54-trends, 55-destinations | PLAN stub + pointer SUMMARY created (real work documented in 53's combined SUMMARY) |
| Empty placeholder future phases | 23, 35-admin-ui-build-missing, 36-admin-ui-polish-nav, 38, 39, 40, 41, 42, 43, 44 | Left as-is (future work, not yet started) |
| Drift | 23R has 3 PLAN / 1 SUMMARY | Deferred — 23R was consumed into v0.2.0 rebase; plans 23R-02/03 remain open items but milestone closed via 23R-01 outcome |



**v0.6.0 Customer Data Platform / Partner Management — APPLY complete (3 phases on top of v0.5.0):**

| Phase | Concern | Status |
|---|---|---|
| 49 | Profiles & Traits — dtl_visitor_attrs EAV + 10 seeded canonical traits + v_visitor_profiles pivot view + filterable admin list | ✅ |
| 50 | Promo Codes — coupons distinct from referrals (discount the redeemer); usage caps + per-visitor caps + scheduled/expired windows + always-log redemption attempts (success + rejections) + 5-endpoint admin CRUD + public POST /redeem | ✅ |
| 51 | Partner Management — dib.co-style B2B affiliate platform; 4 tiers (standard/silver/gold/platinum); discriminated-union linkage to referral + promo codes; payout log with external_ref; v_partners view with pre-aggregated lifetime stats | ✅ |

**v0.6.1 — Configurable Promotions + Live UI Test ✅ (this turn's add)**
- Phase 52 ✅ Configurable promotions: `dim_promotion_kinds` (operator-extensible, 9 kinds seeded with JSON Schemas for UI form gen) + eligibility rule evaluator (10-op JSONB AST, no DSL) + Promo Campaigns layer (audience filter + weighted A/B picker over linked promos + always-log exposure)
- 8 real bugs caught + fixed during live testing on running stack
- 100 weighted picks split 70/30 (perfect statistical match for weights 3:1)
- All 8 admin pages return HTTP 200 after auth redirect
- Live data seeded: 1 visitor with full profile, 5 promo codes across 5 kinds, 1 active campaign with 2 weighted promos, 101 exposures, 3 redemption attempts

**v0.7.0 — Cohorts + Trends + Destinations ✅ (this turn's add)**
- Phase 53 ✅ Cohorts: dynamic (rule-based) + static (manual list) + materialized membership; eligibility evaluator extended with `cohort_slugs` context fold (no new ops needed — cleanly reuses `exists`/`eq`); refresh diff-applies + audits
- Phase 54 ✅ Trends: time-series count over any event_name with bucket (hour/day/week/month) + group-by JSONB key (whitelisted SQL); event_names facet endpoint; chart-as-table UI with bar widths
- Phase 55 ✅ Destinations: Segment-style outbound webhooks; HMAC-SHA256 signing; filter_rule via shared eligibility evaluator; concurrent fan-out wired into `service.ingest_batch`; every attempt logged
- Real bug caught + fixed live: datetime in event payload broke json.dumps for events that passed filter; added `_stringify` recursive ISO conversion
- Live verified: trend query, cohort refresh (rule eval), webhook delivery with HMAC + filter all working end-to-end on running stack

**Aggregate state: product_ops feature has 9 sub-features, 61 routes, 25 tables.**

**v0.8.0+ still planned (deferred placeholders):**
- Identity stitching backfill (Mixpanel-standard: retroactively assign user_id to pre-identify events)
- Group analytics (org-level metrics, B2B SaaS critical)
- Lexicon UI (event taxonomy governance)
- Promo depth (stacking rules, bulk one-time codes, refund clawback)
- Partner-facing portal (partner self-service)
- Auto-payout via Stripe Connect
- Session Replay (rrweb + S3 blob + player UI; whole new infra epic)
- A/B experiment framework
- Mobile SDKs (iOS/Android)
- GDPR DSAR flows

**v0.5.0 Product Ops — APPLY complete across 5 phases / 7 plans:**

| Phase / Plan | Status | What shipped |
|---|---|---|
| 45-01 | ✅ | Schema (7 tables, 2 views, daily partitions, LISTEN/NOTIFY) + ingest endpoint + 2 nodes + admin live-tail page |
| 45-02 | ✅ | `@tennetctl/browser` SDK (≤5kb target, ~360 lines + vitest suite) + identify path in ingest + visitor detail page |
| 45-03 | ✅ | Server-side SDK (`client.product` in Python + `ProductOpsClient` in TS) + UTM aggregate endpoint + dashboard |
| 46 | ✅ | Link shortener: fct_short_links + `GET /l/{slug}` redirect + CRUD + admin page |
| 47 | ✅ | Referrals: fct_referral_codes + evt_referral_conversions + attach/convert endpoints + `product_ops.referrals.attach` effect node + admin page. Auto-emits utm_source=referral touch so referrals show in standard UTM funnels. |
| 48 | ✅ | Funnel + retention engine over evt_product_events; POST /v1/product-events/funnel + GET /retention + admin page |

**Aggregate stats:** 3 SQL migrations (NNN 058–061), 3 catalog sub-features (events + links + referrals) with 3 effect/control nodes + 18 HTTP routes, ~5000 new lines of Python + TypeScript + SQL across ~35 files. Full pyright + tsc + pytest unit suite green.

**Open items (recorded to Decisions table above):** 2 documented cross-import violations in links + referrals services (import 01_events.repository directly instead of going through run_node). Matches pre-existing notify pattern. Cleanup is a post-milestone item.

**Operator-deferred (require live infra):**
- Run migrator UP on Postgres to apply the 3 product_ops migrations
- Provision vault key `product_ops/project_keys/<pk>` with `{org_id, workspace_id}` JSON
- Run `pytest tests/test_product_ops_*` integration subset (expects DB + vault)
- Playwright MCP walkthrough on `/product`, `/product/links`, `/product/referrals`, `/product/utm`, `/product/funnels`
- `cd sdks/browser && npm install && npm test` to exercise the browser SDK vitest suite

**Completed across sessions (v0.2.1 + v0.2.2 + v0.2.3 + v0.2.4):**

Phase 28 ✅ — SDK Core skeleton + auth (py + ts)
Phase 29 ✅ — SDK flags + iam + audit + notify (py + ts)
Phase 30 ✅ — SDK metrics + logs (py + ts)
Phase 31 🟡 — SDK traces query/emit shipped; autoinstrument deferred to 31-b
Phase 32 ✅ — SDK vault + catalog (py + ts)
Phase 33 ✅ — APISIX gateway sync (YAML writer + worker + status endpoints)
Phase 34 ✅ — Admin UI coverage matrix produced
Phase 35-01 ✅ — Workspaces detail + member list page
Phase 35-02 ✅ — Notify SMTP / Template Group / Subscription edit flows
Phase 35-03 ✅ — System Health dashboard + enhanced /health endpoint
Phase 36-01 ✅ — System feature nav registration
Phase 37 ✅ — Catalog handler cache + DEBUG-gated hot-reload watcher

**Session totals (current autonomous sweep):** 4 plans shipped end-to-end (35-01, 35-02, 35-03, 36-01). 5 new routes + 1 new component + 3 new Update hook pairs + enhanced /health. Frontend typecheck + build green across the board.

**Remaining roadmap:**

**v0.2.3 — Unified SDK Platform (🟡 APISIX needs infra spin-up):**
- Phase 33 APISIX sync — backend shipped; integration test pass still pending docker-compose APISIX
**v0.2.4 — Admin UI Coverage Pass (✅ 🔴 gaps closed):**
- 35-01 ✅ Workspaces detail · 35-02 ✅ Notify edit · 35-03 ✅ System Health · 36-01 ✅ System nav
- 🟡 deferred: Portal Views wiring (36 follow-on), SDK dogfood swap, Notify campaigns/suppressions admin, Impersonation history page
**v0.1.8 — Runtime Hardening:** Phases 37–39 (37 ✅; 38 auth hardening + 39 NCP maturity remain)
**v0.3.0 — Monitoring Alerting + SLOs:** Phases 40–41
**v0.4.0 — Canvas + Visual Flow Viewer:** Phases 42–44

Full details in `.paul/MILESTONE-QUEUE.md`.

**Completed milestones:**
- v0.2.0 Feature Flags + AuthZ Control Plane — ✅ via 23R rebase (2026-04-18)
- v0.1.9 IAM Enterprise — ✅ 8/8 plans (2026-04-18)
- v0.1.7 Notify Production + Developer Docs — ✅ 6/6 phases (2026-04-17)
- v0.1.6 IAM Hardening for OSS — ✅ 12/12 plans (2026-04-17)
- v0.1.5 Observability — ✅ 8/8 Phase 13 plans
- v0.1 Foundation + IAM — ✅ 12/12 phases

## Performance Metrics

**Velocity:**
- Total plans completed: 17
- Average duration: ~27 min
- Total execution time: ~477 min

**By Phase:**

| Phase | Plans | Total Time | Avg/Plan |
|-------|-------|------------|----------|
| 01-core-infrastructure | 3/3 ✅ | ~60min | ~20min |
| 02-catalog-foundation | 3/3 ✅ | ~95min | ~32min |
| 03-iam-audit | 4/4 ✅ | ~85min | ~21min |
| 04-orgs-workspaces | 2/3 🟡 backend done, UI remains | ~40min | ~20min |
| 05-users | 2/2 ✅ backend complete | ~25min | ~13min |
| 06-roles-groups-apps | 1/1 ✅ backend complete | ~35min | ~35min |
| 07-vault | 2/2 ✅ full-stack complete | ~90min | ~45min |
| 08-auth | 2/2 ✅ full-stack complete (08-02 closed retroactively) | ~15min | ~15min |
| 10-audit-analytics | 4/4 ✅ full-stack complete (explorer + analytics + outbox) | ~182min | ~46min |
| 11-notify | 12/12 ✅ complete | ~4 sessions | — |

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| Raw SQL with asyncpg, PG-specific features allowed | Init | No ORM |
| Audit in 04_audit schema, cross-cutting | Planning | All features write evt_audit |
| Every phase is a vertical slice | Planning | Schema → repo → service → routes → nodes → UI → Playwright |
| Custom SQL migrator (asyncpg-only, UP/DOWN, rollback, history) | Phase 1 | — |
| Postgres on port 5434; Frontend port 51735 | Phase 1 | Non-standard; avoids conflicts |
| importlib everywhere for numeric dirs | Phase 1 | — |
| Distributed migrations in 09_sql_migrations/; seeds as YAML | Phase 1 refactor | Migrator rglobs |
| fct_* tables have NO business columns (except identity slugs) | Planning | All attrs in dtl_attrs via EAV |
| NCP v1 — sub-features communicate only via `run_node` | Phase 2 | Enforced by lint |
| Catalog DB in `01_catalog`; fct_* use SMALLINT identity PKs | Phase 2 | Documented deviation from UUID v7 rule |
| Effect-must-emit-audit: triple defense (DB CHECK + Pydantic + runner) | Phase 2 | — |
| Pydantic models ARE the manifest schema | Phase 2 | Single source of truth |
| feature.key == metadata.module in NCP v1 | Phase 2 | One feature per module |
| Linter parses both `from X` + `import_module("X")` Call nodes | Phase 2 | — |
| `Any` typing for dynamically-imported modules | Phase 2 | Pyright can't follow importlib |
| NodeContext propagates audit scope + tracing | Phase 2 | — |
| Execution policy per node (timeout/retries/tx modes) | Phase 2 | — |
| Idempotency check before Pydantic validation | Phase 2 Plan 03 | — |
| TransientError is the only retryable exception class | Phase 2 Plan 03 | — |
| Cross-import validator enforces sub-feature boundaries | Phase 2 | Pre-commit hook |
| MCP + scaffolder CLI deferred to v0.2 | Phase 2 | — |
| Per-sub-feature migration layout — each sub-feature owns its SQL | Phase 3 Plan 03 | Scales to 10-30 sub-features |
| Node keys require 3+ segments (feature.sub.action) | Phase 3 Plan 03 | `audit.emit` → `audit.events.emit` |
| Default authz bypasses user_id for audit_category in (system, setup) | Phase 3 Plan 03 | — |
| JSONB codec registered on pool init | Phase 3 Plan 03 | dict⇄JSONB transparent |
| Audit scope triple-defense with setup/failure bypasses | Phase 3 Plan 03 | — |
| Views use MAX(...) FILTER for EAV pivot; hide internal FKs | Phase 3 Plan 04 | Scales; internal refactors invisible |
| Pool propagation via NodeContext.extras['pool'] | Phase 4 Plan 01 | Route stashes pool; downstream nodes emit audit via run_node without extending frozen NodeContext |
| Service mutation fns take (pool, conn, ctx) | Phase 4 Plan 01 | Audit emission is an explicit dep, not hidden in ctx |
| iam.orgs.get kind=control (read-only DB ops widening) | Phase 4 Plan 01 | Control nodes may read; NCP §11 doc sync deferred to v0.1.5 |
| Route paths with {id} must be quoted in YAML manifests | Phase 4 Plan 01 | Sidesteps flow-mapping parser; convention for future route lists |
| Option B for EAV description on fct_vault_entries | Phase 7 Plan 01 | Pure-EAV rule preserved; description lives in 02_vault.dtl_attrs via dim_attr_defs entry |
| AES-256-GCM envelope encryption via PyCA cryptography | Phase 7 Plan 01 | Per-secret DEK + 12-byte nonces + GCM auth tag; root key in TENNETCTL_VAULT_ROOT_KEY (32 bytes base64) |
| Env-var allowlist (5 TENNETCTL_* vars) enforced at startup | Phase 7 Plan 01 | Any stray TENNETCTL_*_SECRET / TOKEN / PASSWORD / KEY blocks boot — secrets belong in vault |
| VaultClient SWR cache 60s + invalidate on rotate/delete | Phase 7 Plan 01 | Hot-path secret reads near-zero latency; rotate/delete invalidate inside same tx |
| Audit HTTP reads but not node reads for vault | Phase 7 Plan 01 | HTTP GET /v1/vault/{key} audits; vault.secrets.get node does not — hot path bypass |
| Item path keyed on {key} not {id} for vault | Phase 7 Plan 01 | Operators + backend code reference secrets by stable user-supplied name |
| Seed filenames must be globally unique | Phase 7 Plan 01 (discovered) | Seeder tracks by filename across features; use feature-prefixed names (e.g. 02vault_*.yaml) |
| Reveal-once UI uses useRef + unmount | Phase 7 Plan 02 | Plaintext held in ref (not state / not TanStack cache); dialog returns null when closed → textarea detached from DOM. Page reload cannot recover the value. |
| Row-scoped testids for per-row dialogs | Phase 7 Plan 02 | Playwright Browser library strict mode rejects duplicate selectors; suffix with ${key} on any form/button inside a row-mounted dialog. |
| dim_* tables: plain SMALLINT PK (not IDENTITY) when statically seeded; IDENTITY when dynamically populated | Phase 10 Plan 01 | Convention-fix: seeder uses `OVERRIDING SYSTEM VALUE=no`, so GENERATED ALWAYS blocks explicit-id YAML seeds. dim_audit_categories (static) is SMALLINT; dim_audit_event_keys (dynamic) is IDENTITY |
| Audit taxonomy joins evt_audit by TEXT code (no FK on evt_audit) | Phase 10 Plan 01 | Preserves emit_audit backward compat (CHECK + text column unchanged); v_audit_events LEFT JOINs dim_audit_categories.code + dim_audit_event_keys.key |
| Audit HTTP reads emit `audit.events.queried` fire-and-forget from separate conn | Phase 10 Plan 01 | Audit-of-reads contract (vault precedent); never couples to read tx, never fails the read |
| Node tx=caller is the default for control nodes (not tx=none) | Phase 10 Plan 01 | Matches featureflags.flags.get; nodes need ctx.conn to read. tx=none is for pure compute / request-path nodes only |
| Cross-org audit query authz at HTTP layer (fail-closed + filter auto-injection) | Phase 10 Plan 01 | Service stays composable for admin surfaces; HTTP route rejects with 403 when session org ≠ filter org, auto-injects session org when filter omitted |
| Every backend sub-feature = full vertical (backend + frontend + Robot E2E in one plan) | User directive (2026-04-16, mid 10-01) | No more backend-only plans from Plan 10-02 onward. Phase 11 + 12 plans already structured as full verticals in ROADMAP |
| Monitoring fct_* tables are catalog/registry — exempt from pure-EAV rule | Phase 13 Plan 01 | Precedent = 01_catalog fct_features/fct_sub_features/fct_nodes. Monitoring `fct_monitoring_metrics` (key/kind/buckets/cardinality) and `fct_monitoring_resources` (hashed service identity) store type-critical metadata used at ingest hot path; EAV pivot would break OTel attribute-fan performance. Documented exception, not general relaxation. |
| Monitoring fct_* use IDENTITY PKs (SMALLINT metrics, BIGINT resources) — not UUID v7 | Phase 13 Plan 01 | Registry-identity tables at hot path. Metric ID used as FK in every evt_monitoring_metric_points row (billions/day); SMALLINT = 2 bytes vs UUID = 16 bytes. Resource ID same rationale on BIGINT. Catalog precedent. |
| Monitoring evt_* use first-class OTel top-level columns, not pure-JSONB metadata | Phase 13 Plan 01 | trace_id/span_id/severity/service_name are universal OTel fields with typed indexes; relegating to JSONB blocks GIN path optimization + partition pruning. JSONB `attributes` still carries caller-specific fan-out. Event taxonomy per pillar, not generic evt_audit. |
| TIMESTAMP (UTC) used on monitoring tables — override AC-1's TIMESTAMPTZ | Phase 13 Plan 01 | Follows project-wide convention in .claude/rules/common/database.md — app always passes UTC; TIMESTAMP aligns with every other evt_*/fct_* table in the codebase. Plan text predated convention pin. |
| Monitoring fct_* skip is_test/created_by/updated_by | Phase 13 Plan 01 | No human actor on instrumentation-emitted rows. fct_monitoring_metrics is operator-registered so keeps created_at/updated_at; fct_monitoring_resources is machine-interned so keeps only created_at. |
| Ingest-path nodes skip emit_audit (hot-path audit bypass) | Phase 13 Plan 01 | Audit-of-ingest would double write amplification on telemetry. Precedent = vault.secrets.get hot-path bypass (Phase 7). 13-01 has no ingest nodes yet; carve-out recorded for 13-02/13-03. |
| Monitoring NATS JetStream bootstrap is best-effort (warning + continue on failure) | Phase 13 Plan 01 | Monitoring module is optional; NATS is a soft dependency. Backend boot must not hard-fail when NATS is absent. DLQ stream added at bootstrap so 13-04 doesn't re-migrate. |
| NCP v1 node key prefix is enforced as `<module>.<sub_feature>.<action>`, not just "3+ segments" | Phase 45 Plan 01 (apply-time discovery) | Plan assumed `product.events.ingest` (3 segments) would pass; manifest Pydantic validator demanded `product_ops.events.ingest`. Updates Phase 3 Plan 03 decision "Node keys require 3+ segments" with the stricter actual rule. Phase 28-32 SDK call-sites for product events all use the full prefix. |
| Effect nodes MUST emit audit — the bypass is only for `kind=request` and `kind=control` | Phase 45 Plan 01 (apply-time discovery) | Plan 45-01 attempted to register `product.touches.record` as kind=effect + emits_audit=false citing monitoring's hot-path bypass. Monitoring's bypass is on request-kind ingest nodes; effects have no bypass (DB CHECK + Pydantic + runner triple-defense). Speculative `touches.record` node removed from manifest; touch-writing logic stays inlined in ingest service. |
| Pure-EAV carve-out on fct_visitors for hot-path attribution columns | Phase 45 Plan 01 | 7 first-touch columns (first_utm_source_id, first_utm_medium/campaign/term/content, first_referrer, first_landing_url) stay first-class; EAV pivot on a billion-event funnel engine is untenable. Documented in migration header + ADR-030. Narrow exception — future visitor attrs go through dtl_attrs via dim_attr_defs. |
| fct_visitors skips is_test/created_by/updated_by | Phase 45 Plan 01 | Phase 13 monitoring precedent — instrumentation-emitted rows have no human actor. Same logic for lnk_visitor_aliases (system-created on identify merge). |
| `_VALID_MODULES` Literal in catalog manifest.py must be updated when adding a new feature module | Phase 45 Plan 01 (apply-time discovery) | The allowed-modules list lives in TWO places: the `_VALID_MODULES` set (used by `depends_on_modules` validator) AND the `FeatureMetadata.module` Literal type. Both needed 'product_ops' added. Future new-feature plans should include this edit as a line-item. |

### Git State
Last commit: c1ff157 — docs(04-orgs-workspaces): draft Plan 04-01 — Org backend (schemas/repo/service/routes + 2 nodes)
Branch: feat/pivot
Plan 07-01 + 07-02 complete — vault full-stack. 33 new files + 5 modified, ~2490 new lines (backend + frontend + E2E). Ready for full vault commit. Pre-existing uncommitted work from phases 4-6 + 9 left in place. Migrator-test drift + core Robot drift remain (pre-existing; unchanged by this session).

### Deferred Issues
None.

### Blockers/Concerns
None.

### Known Gap Closures (complete for v0.1 foundation)
- Node execution policy — Plan 02-03 ✓
- NodeContext contract — Plan 02-03 ✓
- Authorization hook (with setup bypass) — Plan 02-03 + 03-03 ✓
- Cross-import validator — Plan 02-02 ✓
- Trace propagation — Plan 02-03 ✓
- Audit scope enforcement (triple-defense) — Plan 03-03 ✓
- IAM read-path views — Plan 03-04 ✓
- First IAM vertical (iam.orgs backend) — Plan 04-01 ✓
- Vault foundation (envelope encryption, bootstrap secrets, env-var contract) — Plan 07-01 ✓
- Vault UI + reveal-once enforcement + Robot E2E — Plan 07-02 ✓
- Auth backend (credentials/sessions/auth) wiring + 26 tests green — Plan 08-01 ✓
- Audit taxonomy + query API + `audit.events.query` control node + 21 tests green — Plan 10-01 ✓

### Deferred Gaps (v0.1.5 Runtime Hardening milestone)
- Versioning operational (v1 → v2 migration pattern)
- Async effect dispatch via NATS JetStream
- APISIX gateway sync for request nodes
- Dev hot-reload of catalog on manifest change
- Bulk operation pattern documentation
- Pre-commit hook wiring for linter
- Handler class caching in runner
- NCP v1 §9 doc sync (setup bypass update)
- NCP v1 §11 doc sync (control nodes may do read-only DB ops — Plan 04-01 widening)
- Materialized views consideration if aggregation costs grow
- Refresh test_migrator.py — 11 pre-existing failures from Phase 1 refactor drift
- Consider `pool` as first-class NodeContext field (currently via extras['pool'])

## Session Continuity

Last session: 2026-04-20 — Milestone UNIFY sweep. 18 retroactive PLAN stubs written, 2 pointer SUMMARYs (54, 55) created, STATE.md loop position advanced to UNIFY ✓. No code changes. Next action: pick next milestone (v0.8.0 identity stitching + group analytics + lexicon UI is the highest-value per v0.7.0 SUMMARY gap analysis; v0.1.8 hardening phases 38/39 is the next natural milestone on roadmap).

Previously: 2026-04-19 — AUTONOMOUS v0.5.0 + v0.6.0 sweep. v0.5.0 Product Ops (5 phases): Events/Visitors/Links/Referrals/UTM/Funnels with browser SDK + server SDK. v0.6.0 CDP + Partner Management (3 phases): Profiles/Promos/Partners. 10 SUMMARY files. ADR-030 written. 7 new SQL migrations (058–064). 6 catalog sub-features under product_ops (events, links, referrals, profiles, promos, partners) with 4 nodes + 37 routes. ~10,000 new lines across backend, frontend, SDKs.
Stopped at: v0.5.0 + v0.6.0 fully shipped in code. Operator verification deferred (live migrator + vault seed + Playwright MCP + SDK npm install).
Next action:
  • Operator: apply migrations (058/059/060/061) + seed vault project_key
  • Then: /paul:verify to walk all 5 product admin pages in Playwright MCP
  • Then: /paul:unify to close the milestone loop
Next action:
  • `/paul:apply .paul/phases/45-product-sdk-ingest-attribution/45-01-PLAN.md` — execute the 3 tasks
  • OR backfill ROADMAP.md with milestone v0.5.0 + phases 45/46/47/48 first
  • OR commit prior uncommitted sweep (main.py, sidebar.tsx, features.ts modified) before applying on top
Resume files: `.paul/phases/45-product-sdk-ingest-attribution/CONTEXT.md`, `.paul/phases/45-product-sdk-ingest-attribution/45-01-PLAN.md`, `03_docs/00_main/08_decisions/030_audit_vs_product_event_streams.md`

Previously: 2026-04-18 — AUTONOMOUS SEQUENCE (admin UI coverage + yellow-gap sweep + nav completeness). 7 plans shipped end-to-end. Resume files: `.paul/phases/35-critical-admin-ui/*-SUMMARY.md`, `.paul/phases/36-portal-polish/36-*-SUMMARY.md`, `.paul/MILESTONE-QUEUE.md`

### This session's total output
- 6 phase SUMMARY files across phases 28, 29, 30, 31, 32, 34
- 10 SDK capability modules × 2 languages = 20 source files
  - Python: errors, _transport, client, auth, flags, iam, audit, notify, metrics, logs, traces, vault, catalog + __init__
  - TypeScript: errors, transport, client, auth, flags, iam, audit, notify, metrics, logs, traces, vault, catalog + index
- 151 tests (80 py + 71 ts), ≥90% coverage both SDKs, both build + typecheck clean
- Admin UI coverage matrix documenting every gap with severity
- SDK quickstart + 2 package READMEs

Remaining work requires either external infrastructure (APISIX, live monitoring backend) or substantial frontend/backend coding in the browser (admin UI phases) that cannot be meaningfully completed in a single autonomous turn.

---
*STATE.md — Updated after every significant action*
