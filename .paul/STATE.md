# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-16)

**Core value:** Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in. **Empire thesis (2026-04-24):** tennetctl is the OS for self-hosted business SaaS apps; somaerp + somacrm + future apps are thin shells consuming tennetctl primitives. No external SaaS dependencies, ever.
**Current focus:** v0.9.0 somaerp Foundation — Phase 56 — Plan 56-01 (Documentation Suite, zero code) created 2026-04-24, awaiting APPLY. Soma Delights = first tenant. v0.8.0 GDPR DSAR shipped 2026-04-23.

## Current Position

Milestone: **v0.9.0 somaerp Foundation** (Phase 56)
Phase: **56 — somaerp Foundation** (12 plans planned: 56-01 docs + 56-02 base infra + 56-03..12 verticals)
Plan: **56-01 PLAN created 2026-04-24** / 56-02..12 not yet drafted
Status: PLAN created, ready for APPLY. 56-01 is documentation only (zero code) — produces ~42 markdown files under apps/somaerp/03_docs/ that serve as spec for plans 56-02 through 56-12. Architecture: hybrid hardcoded ERP skeleton + JSONB properties extension; tennetctl backbone for auth/IAM/audit/vault/notify; multi-kitchen multi-region scale-safe from day 1.

Previously: v0.8.0 SHIPPED 2026-04-23. Live verification passed all 4 ACs end-to-end on running stack:
- AC1 ✓ 16_fct_sessions referenced correctly in DSAR repo (sessions exported)
- AC2 ✓ Encrypted payload persisted: 3396B ciphertext + 12B nonce in 20_dtl_dsar_payloads
- AC3 ✓ Download endpoint decrypts correctly — returns full user JSON (user, attrs, sessions, credentials, org_memberships, role_assignments, audit_events)
- AC4 ✓ 6 DSAR audit events via run_node: export_requested + export_downloaded confirmed in /v1/audit-events
Vault keys confirmed: auth.argon2.pepper + iam.dsar.export_dek_v1 present in 02_vault schema.
Migration 083 applied 2026-04-22. All 17 migrations applied, DB up to date.
Frontend redesign also committed: 86 files, Palantir operational UI across 62 pages (IBM Plex fonts, CSS design system, WorkspaceContext, cross-feature navigation, StatCards).

Last activity: 2026-04-24 — PHASE 56 COMPLETE. 13/13 plans UNIFIED. somaerp v0.9.0 Foundation end-to-end live. All 4 services running. paul.json bumped to phase.status=complete, milestone.status=complete. Recipe seed removed mid-sweep per user directive (memory rule saved at feedback_never_seed_recipes.md). User can now create all tenant-specific entities (recipes, batches, procurement runs, customers, subscriptions, delivery routes, QC checkpoints, inventory movements) via the UI.

Next action: Open questions for v0.9.1 or v0.10.0:
(a) Pytest backfill plan (56-04b/56-05b/... deferred test suites) — a dedicated v0.9.1 hardening plan to write pytest coverage across all 14 sub-features.
(b) Error-mapping cross-cutting plan (asyncpg constraint violations → typed HTTP codes 409/422 throughout; currently raw 500 on unique violations in most sub-features).
(c) RBAC scope enforcement cross-cutting plan (geography.read/.write/.admin etc. — currently all endpoints accept any authenticated request with workspace_id).
(d) Proper login page for somaerp (replace localStorage.somaerp_token dev convenience with an OAuth-style redirect to tennetctl or embedded sign-in flow).
(e) Photo upload for QC + delivery stops (currently photo_vault_key is a text placeholder; needs tennetctl vault blob primitive or direct object-storage integration).
(f) Scheduled delivery generator (daily cron that auto-creates fct_delivery_runs + stops from active subscriptions given their frequency).
(g) somacrm — the second app on the tennetctl backbone (template now proven: 13 plans shipped for somaerp; somacrm probably 6-8 plans).

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
  ✓        ✓        ✓    [Plan 56-13 UNIFIED 2026-04-24 — PHASE 56 COMPLETE]
```

**PHASE 56 somaerp Foundation — COMPLETE.** All 13 plans UNIFIED (56-01 through 56-13). Milestone v0.9.0 shipped end-to-end. Stack live: tennetctl-be:51734 + tennetctl-fe:51735 + somaerp-be:51736 + somaerp-fe:51737. ~60 database tables + views in schema "11_somaerp". ~80 backend endpoints across 14 sub-features. ~35 frontend pages.

**ERP capabilities shipped:**
- Geography + capacity (multi-kitchen, multi-region, ADR-003 time-windowed capacity)
- Catalog (product lines + products + variants + wellness tags)
- Supply (raw materials + suppliers + primary-supplier links with cost history)
- Recipes with versioning + BOM cost rollup (live client-side cost tweaking)
- Equipment catalog + kitchen-equipment + step-equipment links
- Quality Control (polymorphic checkpoints + immutable check events)
- Procurement runs + Inventory movements + **MRP-lite BOM-explosion planner** (POST /inventory/plan for "raw materials needed for any given day")
- Production batches — 4 AM mobile tracker with auto-emit inventory consumption on complete + live yield/COGS/margin
- Customers + Subscription Plans + Subscriptions with state machine + event log
- Delivery Routes + Riders + Runs + Rider mobile stops UI
- Reporting: 7 cross-layer views (dashboard/yield/COGS/inventory alerts/procurement spend/revenue projection/FSSAI compliance CSV)

**Seed policy honored throughout:** Only universal `dim_*` tables seeded (regions, units, categories, tags, source types, rider roles, subscription frequencies, equipment categories, QC check types/stages/outcomes). ZERO tenant-specific seeds (no recipes, no batches, no checkpoints, no customers, no subscriptions, no routes, no runs) per user directive 2026-04-24.

**User expansion (2026-04-24, late-session):** In addition to the 13-plan phase, user wants: (1) recipe-value playground — tweak recipe ingredient quantities, see COGS rollup (56-07 + cross-cut into a /ops playground); (2) raw-material cost history (extend current target_unit_cost with price-history table in 56-09 procurement); (3) "exact raw materials needed for any given day" — procurement planner BOM-explosion workflow (subscriptions × recipes → rollup → shopping list, in 56-09); (4) "exact equipment needed for any given day" — NEW concept: Equipment sub-feature (dim_equipment_types, fct_equipment, lnk_recipe_step_equipment) to be added to 56-07 recipes or inserted as 56-06b. Think Salesforce/SAP lite: BOM + MRP (light) + resource planning + costing rollups. Document in 56-CONTEXT.md as expanded-scope when this session ends.

**Plan 56-05 APPLY+UNIFY result:**
- Backend: migration + 3 seed YAMLs + 2 sub-features (30_raw_materials + 35_suppliers) + 2 router mounts + manifest — 16 files
- Frontend: 5 /supply pages + appended types/lib — 8 files
- Live: 17 raw materials + 4 suppliers + 21 successful POSTs; MCP verified via 2 screenshots
- Key deviation: lnk_raw_material_suppliers IS MUTABLE (has updated_at/updated_by) per spec, first link-table exception to immutable-lnk rule; hard-delete (no soft-delete) since no deleted_at col; service adds `.material_supplier.updated` audit key beyond spec's 3
- SUMMARY: .paul/phases/56-somaerp-foundation/56-05-SUMMARY.md
- Phase 56 total data in DB now: 1 region + 2 locations + 1 kitchen + 1 zone + 4 categories + 7 tags + 1 product_line + 6 products + 8 raw_material_categories + 7 units + 6 source_types + 17 raw_materials + 4 suppliers

**Plan 56-04 APPLY+UNIFY result:**
- Backend: migration (5 tables + 1 link + 3 views) + 2 seed YAMLs + 2 sub-features (20_product_lines, 25_products) + main.py mount + manifest — 15 files
- Frontend: 5 catalog pages + appended types/api.ts + lib/api.ts — 5 files
- Live application: Cold-Pressed Drinks product line + 6 Soma Delights SKUs created via API with correct wellness tags, rendered in UI with pills
- MCP walk: /catalog/products + /catalog/product-lines verified with authed session (fresh token after backend restart)
- AC-4 pytest DEFERRED to 56-04b (patterns duplicate 56-03; backend proven live)
- Deviations: migration parser `-- UP ====` separator issue (fixed inline); dev-server cache cleared after Task 2's npm build; TIMESTAMP over TIMESTAMPTZ (56-03 precedent); v_products carries category_id additively
- SUMMARY: .paul/phases/56-somaerp-foundation/56-04-SUMMARY.md

**Plan 56-03 APPLY result (2026-04-24):**
- Task 1 ✓ DONE — Backend: migration (4 tables + 4 views, NO capacity) + dim_regions seed (IN-TG) + 3 sub-features (10_locations, 15_kitchens, 17_service_zones, 5-file pattern each) + main.py mount + manifest update. 19 files.
- Task 2 ✓ DONE — Frontend: 7 pages under /geography/* + updated page.tsx + appended types/api.ts + appended lib/api.ts. tsc + npm build green. 9 static routes.
- Task 3 ✓ DONE — Real-DB pytest suite: conftest.py (session pool + migration replay + seed + TestAuthMiddleware) + 3 test files. **32/32 tests pass in 0.9s** (29 new geography + 3 existing health). Zero surgical fixes to Task 1/2 code.
- All 4 ACs PASS (verified in SUMMARY).
- Documented deviations: (a) fct_* JSONB columns per ADR-002 hybrid EAV (3rd documented exception); (b) TIMESTAMP over TIMESTAMPTZ per project rule (spec said TIMESTAMPTZ); (c) kitchen DELETE 30-day production_batches guard TODO(56-10); (d) RBAC scope checks deferred to future cross-cutting plan; (e) duplicate-slug → 500 not 409 (error-mapping polish deferred); (f) Pyright importlib type blind spot (known limitation).
- SUMMARY: .paul/phases/56-somaerp-foundation/56-03-SUMMARY.md

**Plan 56-03 scope (geography MINUS capacity):**
- Task 1: Backend — migration (4 tables: dim_regions + fct_locations + fct_kitchens + fct_service_zones + 4 views) + 3 sub-features (10_locations, 15_kitchens, 17_service_zones) + manifest update + main.py mount + dim_regions seed (IN-TG)
- Task 2: Frontend — 7 pages under /geography/* + appended types/api.ts (Region, Location, Kitchen, ServiceZone) + appended lib/api.ts wrappers
- Task 3: Real-DB pytest suite (conftest with session-scoped pool against tennetctl_test on port 5434) + boot verification
- Defers: capacity → 56-06; cross-layer "30-day production_batches" kitchen-DELETE guard → TODO (56-10); RBAC scope checks → future cross-cutting plan

**Plan 56-02 APPLY result (2026-04-24):**
- Task 1 ✓ DONE — Backend scaffold (21 files): main.py + 8-file 01_core/ + 00_health 5-file sub-feature + scripts/migrator + feature.manifest.yaml (key 11_somaerp) + schema migration. All Python files parse, manifest contract valid, env vars (9 required) all present.
- Task 2 ✓ DONE — Frontend scaffold (10 files): Next.js 15 + React 19 + Tailwind v3 + landing page with live health widget + types/api.ts + lib/api.ts. npm install + tsc --noEmit + npm run build all green.
- Task 3 ✓ DONE — Tests + README + boot verification (3 files): 3 pytest cases pass in 0.18s, README explains run flow. Zero deviations from Tasks 1/2.
- All 3 ACs PASS (verified in SUMMARY).
- Documented deviations: (a) Next 15+React 19 vs solsocial Next 14+React 18 (plan-driven); (b) env var naming conflict between plan (TENNETCTL_BASE_URL) and spec doc (SOMAERP_TENNETCTL_BASE_URL) — followed plan; (c) Pyright lint debt on database.py:43 (asyncpg type-stub mismatch, runtime fine); (d) tennetctl catalog scanner doesn't auto-discover apps/ manifests — manifest is doc-only until extended; (e) Next 15.1.6 CVE — bump in next plan.
- SUMMARY: .paul/phases/56-somaerp-foundation/56-02-SUMMARY.md

**Plan 56-02 scope (somaerp base infrastructure scaffold):**
- Task 1: Backend scaffold — main.py + 8-file 01_core/ + 00_health 5-file sub-feature + scripts/migrator wrapper + feature.manifest.yaml (key 11_somaerp) + schema namespace migration ("11_somaerp")
- Task 2: Frontend scaffold — Next.js 15 + tsconfig strict + Tailwind + landing page + types/api.ts + lib/api.ts (port 51737)
- Task 3: Smoke tests + README — 3 pytest cases (health envelope, tennetctl proxy field, root liveness) + apps/somaerp/README.md operator guide
- Boundaries: zero business-logic sub-features (those start in 56-03); zero tennetctl modifications; zero seeds (Soma Delights tenant ships in 56-03 onwards)
- Reads from: 56-01 docs at apps/somaerp/03_docs/00_main/01_architecture.md + 04_integration/00_tennetctl_proxy_pattern.md as spec; apps/solsocial/ as proven template

**Plan 56-01 APPLY+UNIFY result (2026-04-24):**
- Task 1: ✓ DONE — 12 foundational docs (overview, architecture, tenant_model, 8 ADRs, tennetctl proxy pattern)
- Task 2: ✓ DONE — 20 docs (data_model overview + 9 layer schema specs + api_design conventions + 9 layer endpoint specs)
- Task 3: ✓ DONE — 10 docs (4 scaling strategy + 5 tennetctl integration + Soma Delights tenant config)
- Output: 42 markdown files under apps/somaerp/03_docs/, 5,981 lines total. Zero code. Zero external SaaS dependencies (verified). All 8 ADRs Status: ACCEPTED. tenant_id present in all 10 data_model layers. All 4 ACs PASS.
- Documented deviations (logged for UNIFY): (a) ADR-002 introduces 2nd documented exception to project pure-EAV rule — scoped to app layer; (b) evt_delivery_runs mixes append-only with lifecycle started_at/completed_at — flagged for plan 56-11 reconsideration; (c) dim_qc_checkpoints + dim_subscription_plans use tenant_id + UUID PK — flagged for potential dim→fct rename at audit time; (d) v0.1 vault blob storage uses base64-in-vault stopgap pending true blob primitive (deferred to v0.10).
- Operator-confirmation TBDs in tenant config: KPHB kitchen address, FSSAI license number, founder iam user_id, specific local farm/bottle/print-shop supplier names.
- SUMMARY: .paul/phases/56-somaerp-foundation/56-01-SUMMARY.md

Previously: Plan 45-01c UNIFIED 2026-04-22.

**Plan 45-01c scope (v0.8.0 ship gate):**
- Task 1: Fix sessions table name (12_fct_sessions → 16_fct_sessions) in DSAR repository
- Task 2: AES-256-GCM encrypted export payloads in new 22_dtl_dsar_payloads table; DEK from vault
- Task 3: Replace inline SQL audit INSERTs with run_node("audit.events.emit", ...)
- Task 4: Register iam.dsar sub-feature in backend/02_features/03_iam/feature.manifest.yaml
Bonus triage (audit retention + authz helpers out-of-plan code) deferred to 45-01d. Previous loop closure:

Phase 40-41 closed: 40-01/02/03 (monitoring alerting), 41-01 (SLO definition). All summaries written. v0.3.0 shipped.  
Phase 42-44 closed: 42-01/02 (canvas flow schema), 43-01/02 (backend), 44-01 (frontend). v0.4.0 shipped.

Current: Plan 45-01 shipped code but with structural drift; 45-01-SUMMARY.md documents 3 schema mismatches (migration/repo/tests), worker not wired, vault stubbed, audit bypasses run_node, + 3 bonus out-of-plan sub-features (audit retention, authz helpers). v0.8.0 gate BLOCKED pending 45-01-REWORK.

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
| somaerp uses HYBRID hardcoded ERP skeleton + `properties JSONB` extension on every fct_* (NOT pure entity_type_definitions framework). 2nd documented exception to project pure-EAV rule, scoped to APP layer only — tennetctl primitives still follow strict pure-EAV. | Phase 56 Plan 01 (ADR-002) | Allows hot-path indexed queries on real columns (today's batches at this kitchen, current inventory by raw material) while preserving per-tenant extensibility via JSONB. Future apps must opt in to either pure-EAV (tennetctl-primitive-style) or hybrid (somaerp-style); not silent default. Hardcoded skeleton column promoted to real-column when 3+ tenants use the same JSONB field with the same semantics. |
| somaerp tenant_id IS the tennetctl workspace_id — no new somaerp.tenants table | Phase 56 Plan 01 (ADR-001) | Reuses tennetctl 03_iam workspace primitives (RBAC, audit scope, GDPR DSAR) for free. Soma Delights = workspace #1 in the user's tennetctl org. Other apps (somacrm, future) follow the same pattern; same workspace can be a tenant of multiple apps. |
| somaerp kitchen capacity is per (kitchen × product_line × time_window) with valid_from/valid_to history | Phase 56 Plan 01 (ADR-003) | One kitchen can do 200 cold-pressed bottles between 4-8 AM AND 50 fermented drinks between 6-10 AM. Capacity changes over time (hire staff, upgrade equipment) stay queryable historically. Demand-vs-capacity check is a window-scoped point-in-time query. |
| somaerp recipes are versioned (draft/active/archived); production_batches reference EXACT recipe_id used; kitchen-specific overrides via lnk_kitchen_recipe_overrides | Phase 56 Plan 01 (ADR-004) | FSSAI traceability requires knowing the exact recipe used for any past batch. Recipes are immutable once active; new versions ship as new rows. Kitchen overrides allow regional variation (Hyderabad vs future Bangalore kitchen) without forking the canonical recipe. |
| somaerp QC modeled as multi-stage (pre/in/post/fssai) dim_qc_checkpoints + immutable evt_qc_checks; photos via tennetctl vault | Phase 56 Plan 01 (ADR-005) | FSSAI compliance + audit trail needs immutable per-check event log. v0.1 vault blob storage = base64-in-vault stopgap (vault is k/v); true blob primitive deferred to v0.10. Photos stored as vault keys referenced from evt_qc_checks.photo_vault_key. |
| somaerp procurement_runs + inventory_movements are append-only; v_inventory_current view computes stock; lot tracking on receipts for FSSAI traceability | Phase 56 Plan 01 (ADR-006) | Append-only event log = unforgeable history. Lot tracking on receipts ties any production batch back to the specific raw material lot in case of a complaint. v_inventory_current computes current stock from movements, no separate stock table to drift. |
| somaerp production batch state machine: planned → in_progress → completed | cancelled. fct_production_batches references kitchen+product+recipe+planned/actual_qty; computed yield/COGS NOT stored | Phase 56 Plan 01 (ADR-007) | State machine is the simplest model that supports the 4 AM tracker workflow. Computed columns NOT stored — yield % and COGS/bottle are derived from ingredient_consumption + actual_qty in v_batch_summary view. Storing them would create denormalization drift. |
| somaerp NEVER reimplements auth, IAM, audit, vault, notify — always proxies to tennetctl via apps/somaerp/backend/01_core/tennetctl_client.py (solsocial precedent) | Phase 56 Plan 01 (ADR-008) | Empire thesis enforcement at the architectural layer. Same pattern as solsocial. Customer entities (juice-buyers in fct_customers) are SEPARATE from tennetctl iam users (operators/staff/admins). |
| evt_delivery_runs has lifecycle started_at/completed_at — flagged minor deviation from strict evt_* no-updated_at convention | Phase 56 Plan 01 (apply-time discovery) | Delivery runs have a real lifecycle (rider departs → returns) that doesn't fit pure event-emission semantics. Plan 56-11 may split into fct_delivery_runs (mutable lifecycle) + evt_delivery_run_events (state-change events) at implementation time. Documented now to prevent silent drift later. |
| dim_qc_checkpoints + dim_subscription_plans use tenant_id + UUID PK (per-tenant catalogs, not global enums) | Phase 56 Plan 01 (apply-time discovery) | Both are tenant-defined catalogs (each tenant has its own QC criteria + subscription plan templates) so they don't fit the global-static dim_* shape (SMALLINT PK, no tenant_id). Kept dim_* prefix for semantic role (definitions). At plan 56-06 + 56-10 implementation time may rename to fct_* for naming consistency with other tenant-scoped tables. |
| somaerp scaffold uses Next.js 15 + React 19 + Tailwind v3 (deviation from solsocial's Next 14 + React 18) | Phase 56 Plan 02 | Plan required `next.config.ts` which is Next 15+; Next 15 requires React 19 peer. Tailwind v3 chosen over v4 because v3 has stable Next 15 PostCSS integration. Future apps can adopt this stack or stay on solsocial's older one. |
| somaerp env vars use TENNETCTL_BASE_URL + TENNETCTL_SERVICE_API_KEY (raw env), NOT the spec doc's SOMAERP_TENNETCTL_BASE_URL + _KEY_FILE pattern | Phase 56 Plan 02 (apply-time discovery) | Plan and spec doc 04_integration/00_tennetctl_proxy_pattern.md disagreed; agent followed plan. Reconcile in 56-03 by either updating the spec doc or migrating the env var names. solsocial uses _KEY_FILE pattern (file path, more secure than raw env); revisit before production deploy. |
| Tests bypass FastAPI lifespan and inject app.state.{config,tennetctl,started_at_monotonic,pool} manually using ASGITransport + AsyncClient pattern | Phase 56 Plan 02 (apply-time pattern) | No real Postgres required for smoke tests; in-process stub TennetctlClient replaces network calls. Reusable pattern for every future sub-feature whose tests don't need DB. Documented in apps/somaerp/backend/tests/test_health.py. |
| somaerp feature.manifest.yaml at apps/somaerp/03_docs/features/11_somaerp/ is documentation-only until tennetctl catalog scanner extends to apps/* paths | Phase 56 Plan 02 (apply-time discovery) | tennetctl catalog scanner currently only scans tennetctl/03_docs/features/. Manifest still serves as the spec for the next tennetctl-side plan that wires apps/ discovery. Until then, somaerp boots without catalog registration (acceptable for a thin app). |
| somaerp Pyright lint debt: database.py acquire_session return type — asyncpg `acquire()` returns PoolConnectionProxy but stub annotation says Connection | Phase 56 Plan 02 (deferred) | Runtime works (3 smoke tests green); types lie. Fix in 56-03 by annotating return type as `AsyncIterator[asyncpg.pool.PoolConnectionProxy]` or using `Connection` cast with type-ignore. Not blocking. |
| somaerp fct_* tables carry JSONB columns (properties, address_jsonb, polygon_jsonb) — 3rd documented exception to pure-EAV rule in `.claude/rules/common/database.md` | Phase 56 Plan 03 | Per ADR-002 hybrid EAV: the somaerp APP layer (not tennetctl primitive) uses hardcoded skeleton + JSONB extension. Spec docs in 56-01 explicitly define these columns. Exceptions (prior): monitoring fct_* (Phase 13), product_ops fct_visitors (Phase 45). All app-layer or registry-layer precedent. |
| somaerp TIMESTAMP (UTC) not TIMESTAMPTZ, CURRENT_TIMESTAMP not now() — followed project rule `.claude/rules/common/database.md` over the 56-01 spec doc | Phase 56 Plan 03 | Spec doc 01_data_model/01_geography.md said TIMESTAMPTZ+now(); project rule says TIMESTAMP+CURRENT_TIMESTAMP. Agent followed project rule for consistency with rest of codebase. Reconcile by updating spec doc (lower-priority doc-polish item) OR updating project rule for apps/. |
| Kitchen DELETE 30-day production_batches dependency guard deferred with `# TODO(56-10)` in 15_kitchens/service.py | Phase 56 Plan 03 | fct_production_batches table doesn't exist until 56-10. Guard activates then. Documented skip prevents silent drift. |
| somaerp RBAC scope checks (geography.read/.write/.admin) deferred to future cross-cutting plan — v0 accepts any authenticated request with workspace_id | Phase 56 Plan 03 | Full RBAC wire-up is a tennetctl-side cross-cutting concern (app-level permissions registered via manifest + AccessContext resolver). Not blocking for first tenant (Soma Delights operator is admin-all). |
| somaerp unique-slug constraint violations bubble as HTTP 500 (asyncpg.UniqueViolationError unmapped) — deferred to future cross-cutting error-mapping plan | Phase 56 Plan 03 | Proper fix: map Postgres constraint violations (unique, foreign_key, check) to typed HTTP codes (409 DUPLICATE, 422 INVALID_REFERENCE, 422 INVALID_VALUE). Test asserts status_code >= 400 for now. |
| somaerp test fixture pattern: replace SessionProxyMiddleware with TestAuthMiddleware that reads X-Test-Workspace-Id / X-Test-User-Id / etc headers → request.state | Phase 56 Plan 03 (apply-time pattern) | Tests don't need tennetctl auth running; custom headers inject the scope. Reusable for every future sub-feature test file. Documented in conftest.py. |
| somaerp audit emission setup-mode bootstrap: when user_id is None, use audit category=setup + zero-sentinel UUID in created_by/updated_by to satisfy NOT NULL constraint | Phase 56 Plan 03 (apply-time pattern) | Matches tennetctl audit scope bypass for setup category. Enables first-tenant seeding before any user exists. |
| somaerp frontend Bearer auth: lib/api.ts reads `localStorage.somaerp_token` and injects `Authorization: Bearer ${token}` on every fetch — dev-convenience; formal login page is a future plan | Phase 56 Plan 03 live-verification | Frontend-to-backend auth was unplanned in 56-02/56-03. Without it, somaerp UI only renders error states. Minimal 15-line patch to apiFetch; no hooks, no login flow yet. Future 56-auth plan ships: (a) tennetctl-driven sign-in redirect or OAuth-style flow, (b) token refresh, (c) sign-out, (d) tenant switcher. For v0.1 tooling development: curl+localStorage pairing is sufficient and consistent with "simple but reliable" user preference. |
| Full 4-service stack E2E live-verified 2026-04-24 via MCP Playwright: Hyderabad + KPHB Home Kitchen + KPHB Cluster 1 created via API; Bangalore created via UI form submission | Phase 56 Plan 03 live-verification | Proves tennetctl-auth → somaerp-backend auth scope extraction → somaerp-frontend Bearer injection → DB write → UI list refresh all wired correctly. First Soma Delights tenant data real in DB. 9 MCP screenshots in .playwright-mcp/. |

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

Last session: 2026-04-22 — Plan 45-01c UNIFY. SUMMARY.md already existed from APPLY (4/4 ACs static PASS); this session reconciled STATE.md + paul.json to reflect UNIFY ✓. No new code changes. Operator carry-forward (vault DEK seed + migration 083 apply + live-stack verify) remains before v0.8.0 can ship. Resume file: `.paul/phases/45-gdpr-dsar/45-01c-SUMMARY.md`.

Previously: 2026-04-21 — Phase 45-01 UNIFY. Reconciled plan vs. actual after discovering 45-01 code was committed (a1fa4a0..a4604ec) but never verified. SUMMARY.md flags: migration 071 creates TEXT-CHECK schema; repository queries `65_evt_dsar_jobs` + `07_dim_dsar_statuses` + `08_dim_dsar_types` (none exist); tests use positional args against kwarg-only repo and insert columns (`org_id`/`user_id`) that don't match actual IAM schema; worker loop (`run_pending_dsar_exports/deletes`) not wired into main.py; vault storage is a TODO; audit emitted via direct SQL INSERT instead of `run_node("audit.events.emit")`. Commit 482c981 also deleted 12 monitoring + IAM migrations from `02_in_progress/` — verify these were already applied before 45-01-REWORK.

Previously: 2026-04-20 — Milestone UNIFY sweep. 18 retroactive PLAN stubs written, 2 pointer SUMMARYs (54, 55) created, STATE.md loop position advanced to UNIFY ✓. No code changes. Next action: pick next milestone (v0.8.0 identity stitching + group analytics + lexicon UI is the highest-value per v0.7.0 SUMMARY gap analysis; v0.1.8 hardening phases 38/39 is the next natural milestone on roadmap).

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
