# Phase Context

**Phase:** 45 — Product SDK + Event Ingest + UTM Attribution
**Generated:** 2026-04-19
**Status:** Ready for planning
**Milestone:** v0.5.0 Product Ops (this is phase 1 of 4)
**Schema:** `10_product_ops` (07 reserved for billing, 08 for llmops, 09 already taken by featureflags)
**Backend module:** `backend/02_features/10_product_ops/`
**Frontend route:** `/product`
**Module gate:** `TENNETCTL_MODULES=...,product_ops` (off by default)
**Reference ADR:** [ADR-030 — Audit vs Product Event Streams](../../../03_docs/00_main/08_decisions/030_audit_vs_product_event_streams.md) (written alongside this context)

---

## Milestone Vision (v0.5.0 Product Ops)

A Mixpanel/PostHog-class **product analytics + acquisition** surface, self-hostable, AGPL, modeled as TennetCTL nodes. Replaces the typical Mixpanel + Bitly + Rewardful + Plausible stack with one module.

**Why now:** Phase 10 already shipped a PostHog-class analytics surface — but only over `evt_audit` (server-side, identified-user only). It cannot answer marketing/growth questions: "How many anonymous visitors from this UTM campaign converted?", "What's the click-through on this short link?", "Which referrer drove the most signups?" Product Ops fills that gap by ingesting upstream visitor signals (page views, custom events, UTM, referrer, click) into a separate event stream optimized for marketing cardinality.

**Boundary vs audit:** Codified in **ADR-030**. `evt_audit` = server-side compliance trail (identified, scope-mandatory). `evt_product_events` = client-side product telemetry (anonymous-first, privacy-defaulted, partitioned). Funnel/retention engine is **shared** — generalized in phase 48.

**Phase split (one shippable concern each):**

| # | Phase | Scope |
|---|-------|-------|
| 45 | Product SDK + Ingest + Attribution | JS browser SDK, `/v1/track`, `fct_visitors`, `evt_product_events`, first+last touch UTM, identify/alias, visitor→user merge |
| 46 | Link Shortener | `fct_short_links` (slug → URL + UTM preset + owner), `GET /l/{slug}` redirect node, click events, bulk create, QR generation |
| 47 | Referrals | `fct_referral_codes` (code → referrer user + reward config), visitor attachment on landing, `evt_referral_conversions`, resolution on signup/purchase. Auto-creates `utm_source=referral&utm_campaign={code}` touch — referrals visible in standard UTM funnels with no special-case UI. |
| 48 | Funnels / Cohorts / Retention on product events | Generalize Phase 10 funnel engine to take a target table (`events.funnel(table=...)`). Add cohort builder + retention matrix UI. Saved views per workspace. |

Session recording / heatmaps (rrweb + blob storage) → out of scope; v0.6.0 candidate.

---

## Goals (this phase, 45)

- **Browser SDK that drops into any web app in <5 lines** — `<script src="...">` + `tnt.init({key, host})` then `tnt.track('event', props)` and `tnt.identify(userId)`. Auto-captures page view + UTM + referrer on init. Bundle target: ≤5kb gzip, zero deps.
- **Anonymous-first identity model** — every visitor gets a stable `visitor_id` cookie (UUID v7) before they sign in. On `identify(userId)`, merge visitor → user (keep visitor_id as alias). Mixpanel-style two-pointer separation; no fake IAM users.
- **First-touch + last-touch attribution** — capture `utm_source/medium/campaign/term/content`, `referrer`, `landing_url` on the visitor's first event; keep last-touch updated on every session start. Multi-touch (linear, time-decay, position-based) deferred to v0.5.x.
- **Postgres-only, partitioned ingest** — `evt_product_events` daily-partitioned (Phase 13 monitoring precedent), pg_cron rollups, retention tiering. No NATS/ClickHouse for v1.
- **Batched `/v1/track` ingest** — SDK queues client-side, flushes on timer + on `pagehide`/`beforeunload` via `navigator.sendBeacon`. Server endpoint accepts an array, validates, fans out to ingest node.
- **Privacy contract enforced by default** — DNT respected, IP truncated to /24 (IPv4) / /48 (IPv6) at ingest, opt-out cookie honored, `email`/`phone` props hashed (SHA-256) unless workspace toggle flips. GDPR consent gate hook (no consent UI shipped — just the gate).
- **Admin UI: live event tail + visitor drilldown** — `/product` page with event stream (LISTEN/NOTIFY tail like audit explorer), per-visitor timeline, per-UTM-campaign visitor + conversion counts.
- **TS + Python SDK parity for server-side `track()`** — `tnt.product.track('order.completed', ...)` from a backend service. Phase 28–32 SDK layout precedent.

## Approach

### Schema layout (`10_product_ops`)

Per CLAUDE.md DB conventions + Phase 13 monitoring precedent for hot-path exception:

- **`dim_event_kinds`** — `(page_view, custom, click, identify, alias, referral_attached)`. SMALLINT PK, statically seeded, plain (not IDENTITY).
- **`dim_attribution_sources`** — utm_source values seen. SMALLINT IDENTITY PK, dynamically populated. Precedent: `dim_audit_event_keys`.
- **`fct_visitors`** — UUID v7 PK, `anonymous_id TEXT UNIQUE`, `user_id UUID NULL` FK, `first_seen`, `last_seen`, plus first-touch attribution top-level columns (`first_utm_source_id`, `first_utm_medium`, `first_utm_campaign`, `first_referrer`, `first_landing_url`). **Documented EAV exception** (Phase 13 monitoring precedent): hot-path attribution columns are first-class for query performance; ADR-030 references this carve-out. All other visitor attrs go to `dtl_attrs`.
- **`lnk_visitor_aliases`** — `(visitor_id, alias_anonymous_id, linked_at)`. Many-to-one. Handles cross-device merge on `identify()`. Keep both anonymous_ids resolving to the same canonical visitor; alias graph wins on race (no merge-conflict resolution needed).
- **`evt_product_events`** — daily-partitioned. Top-level OTel-style columns: `(visitor_id, user_id NULL, session_id NULL, workspace_id, event_kind_id, event_name TEXT, occurred_at TIMESTAMP, page_url, referrer)`. High-cardinality props in JSONB `properties`. No business columns hidden in JSONB beyond user-supplied props.
- **`evt_attribution_touches`** — every UTM/referrer hit, append-only. Daily-partitioned. Joined to `fct_visitors` for first/last touch resolution at query time.

### Read views (Phase 3 EAV-pivot precedent)

- `v_visitors` — exposes attribution as resolved TEXT codes, hides FK columns, MAX(...) FILTER pivot for any `dtl_attrs` rows.
- `v_product_events` — exposes `event_kind` as TEXT, hides `event_kind_id`.

### Nodes (NCP v1)

| Node | Kind | Tx | Notes |
|---|---|---|---|
| `product.events.ingest` | effect | own | Validates batch + writes evt_product_events. Emits **one summary** `audit.events.emit("product.events.ingested", {batch_size, workspace_id})` per batch — not per event. ADR-030 + vault hot-path bypass precedent. |
| `product.visitors.identify` | effect | own | Merges visitor → user, writes alias row, updates user_id on existing visitor row (UPDATE not new row). |
| `product.visitors.get` | control | none | Read-only. Plan 04-01 `iam.orgs.get` widening precedent. |
| `product.attribution.resolve` | control | none | Returns `{first_touch, last_touch}` for a visitor. Used by funnel/retention queries in Phase 48. |
| `product.touches.record` | effect | own | Records a UTM/referrer touch, updates `fct_visitors.last_*`. Called inside `events.ingest` when payload carries UTM. |

### SDKs

- **New package `tnt-js`** (browser) — vanilla TS, no deps, esbuild bundle, target ≤5kb gzip. Cookie + localStorage fallback for visitor_id. Batching + sendBeacon flush. Auto page_view on init.
- **Existing `@tnt/sdk` (TS) + `tnt-sdk` (Python)** — add `.product.track()` namespace mirroring Phase 28 layout. Server-side track flows through audit scope rules (org_id + workspace_id required).

### Ingest endpoint (CLAUDE.md simplicity rule)

- **Single endpoint:** `POST /v1/track` accepting an array of events. No `/identify`, no `/alias`, no `/page` — event `kind` in payload routes via `product.events.ingest` switch-on-kind. ADR-026 minimum-surface.
- Read endpoints: `GET /v1/product/events`, `GET /v1/product/visitors/{id}`, `PATCH /v1/product/visitors/{id}` (5-endpoint shape, only what's needed).

### Hot-path bypasses (formalized in ADR-030)

- Browser ingest: no IAM scope on event rows (anonymous-first). Workspace_id resolved from project key, not from session.
- Per-event audit emission skipped; one summary audit per batch.

### Admin UI

- New `/product` route under existing dashboard. Reuses Phase 10 audit explorer's live-tail + filter-chip components, parametrized on table.
- Visitor detail page: timeline + first/last touch + linked alias list + linked user (if identified).
- UTM dashboard: top campaigns by visitor count + conversion count (where conversion = any event with `is_conversion: true` in props, or — once Phase 47 lands — referral-resolved events).

### Vault for keys (`project_vault_for_config` memory)

- Per-workspace ingest project key stored in vault (`product_ops/{workspace_id}/project_key`).
- Public key embeddable in browser SDK (project-scoped, ingest-only); secret key for server-side track + admin reads.

### TDD + E2E

- pytest backend ≥80% (UCS in `tests/` mirroring backend/ structure).
- Playwright MCP for SDK + UI: drop SDK on a test HTML page in the live browser at port 51735, verify events land, verify UTM captured from query string, verify identify-merge works. NEVER `.spec.ts`/Robot Framework.

## Constraints

- **Self-host friendly:** Postgres only for v1. No NATS/ClickHouse/S3 dependency.
- **AGPL-3:** SDK ships AGPL. Package README clarifies that embedding the SDK in a closed product requires source-disclosure when network-deployed.
- **No PII surprises:** IP truncation default; PII prop hashing default; raw-IP and raw-PII workspace toggles documented.
- **Module-gated:** `core+iam+audit` boots fine when `product_ops` disabled. No hard imports outside `backend/02_features/10_product_ops/`. Cross-import linter (Phase 2 Plan 02) catches violations.
- **Cardinality discipline:** UTM values >256 chars rejected at SDK; **distinct event names per workspace per day capped at 500** (operator-tunable via vault key `product_ops/limits/distinct_event_names_per_day`). Mixpanel free tier ~500, PostHog soft-warns at 100; we land between.
- **Audit scope on backend track:** server-side `tnt.product.track()` flows through normal audit scope rules (org_id + workspace_id mandatory); browser-side ingest is exempt — codified in ADR-030.
- **Non-standard ports** (`feedback_weird_ports`): backend 51734, frontend 51735.

## Resolved Decisions (from prior open-questions)

| Question | Decision |
|---|---|
| Multi-touch attribution model in v1? | **First + last touch only.** Multi-touch deferred to v0.5.x once data validates the shape. |
| Cookie domain for cross-subdomain? | SDK accepts `cookieDomain: '.example.com'` config; defaults to `location.hostname`. |
| Rate limiting on `/v1/track`? | **Coarse per-IP cap in middleware for v1** (sliding window, 1000 events / IP / minute). Real per-visitor token bucket deferred to APISIX once Phase 33 integration ships. |
| Visitor merge race | **Keep both anonymous_ids as aliases of the user.** Alias graph is many-to-one; no canonical-resolution worker needed. |
| Session boundary | **30-min inactivity timeout** (Mixpanel default). New tab does not start a new session. |
| Referral code → UTM behavior (Phase 47 cross-ref) | **Auto-create a `utm_source=referral&utm_campaign={code}` touch** when a referral code attaches to a visitor. Referrals show up in standard UTM funnels with no special-case UI. |
| Schema number collision (08 vs 09)? | **CLAUDE.md table is stale.** Real codebase has 02 vault, 03 iam, 04 audit, 05 monitoring, 06 notify, 09 featureflags. Product_ops takes **10**, leaving 07 (billing) and 08 (llmops) reserved. |
| New ADR for stream split? | **Yes — ADR-030 written**, formalizing the audit-vs-product-events boundary, what's shared (query/funnel engine), and what's separate (write paths, scope contracts, partitioning). |
| Distinct-event-name cap default? | **500 per workspace per day**, operator-tunable via vault. |

## Open Questions (deferred; not blockers)

- **`v_unified_events` view** for cross-stream funnels (signup audit event + product click events in one funnel) — surface in Phase 48 if user demand validates the need.
- **Person-merge worker** PostHog-style — only adopt if simple alias graph proves insufficient in the wild.

## Additional Context

- **Reuse, don't duplicate, Phase 10's funnel engine** — Phase 48 of this milestone refactors `audit.events.funnel` into a generic `events.funnel(table, filters, steps)`. Don't write a parallel `product.events.funnel`.
- **Identity model:** Mixpanel `distinct_id` + `$user_id` two-pointer; PostHog v2 person-merge rejected as too complex for the value.
- **SDK reference:** PostHog-js + OpenPanel SDK for batching, sendBeacon flush, cookie strategy. Reimplement patterns; don't fork (keeps bundle ≤5kb).
- **Why a new feature module instead of extending audit:** see ADR-030 — scope contract incompatibility, cardinality + retention shape divergence, privacy contract divergence.
- **Future v0.6.0 candidates:** session recording (rrweb + blob storage), heatmaps, A/B test conversion glue (already have flag rollouts from v0.2.0; need attribution wiring), revenue + LTV cohorts, multi-touch attribution.

---

*This file is temporary. It informs planning but is not required.*
*Created by /paul:discuss, consumed by /paul:plan.*
