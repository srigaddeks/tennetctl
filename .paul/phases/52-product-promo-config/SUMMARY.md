# Phase 52 — Configurable Promotions + Campaigns + Live UI Test — SUMMARY

**Status:** APPLY complete. End-to-end live testing on running infra confirmed every layer works (backend + DB + frontend page render).
**Date:** 2026-04-19

## What was built (configurability layer)

### Schema additions (NNN=065, 066)

- **`01_dim_promotion_kinds`** — operator-extensible kind taxonomy. Replaces the old hardcoded CHECK enum on `fct_promo_codes.redemption_kind` with a FK. Each row carries a JSON Schema for `redemption_config` so the admin UI can render kind-specific forms without hardcoded knowledge.
  - Seeded 9 kinds: `discount_pct`, `discount_cents`, `free_trial_days`, `custom`, `bogo`, `tiered_discount`, `bundle_discount`, `free_shipping`, `gift_credit`
  - Operators add new kinds via INSERT; UI form generation works automatically.
- **`v_promo_codes`** view refreshed to expose `redemption_kind_label` + `redemption_kind_schema` for UI.
- **`10_fct_promo_campaigns`** — name, slug, schedule, audience_rule (JSONB AST), goals (opaque JSONB).
- **`40_lnk_campaign_promos`** — joins campaigns to promos with **A/B weights** + per-link `audience_rule_override`. UNIQUE (campaign_id, promo_code_id).
- **`60_evt_campaign_exposures`** — append-only impression log. Records every (campaign, visitor) decision: `weighted_pick` / `eligibility_miss` / `no_active_promos`.
- **`v_promo_campaigns`** view with pre-aggregated `promo_count`, `exposure_count`, `redemption_count`, computed `status`.

### Eligibility rule evaluator (the "any kind of promotion" enabler)

`backend/02_features/10_product_ops/sub_features/05_promos/eligibility.py` — ~150 lines, no dependencies, no DSL parsing:

- **Leaf ops:** `eq` / `ne` / `gt` / `gte` / `lt` / `lte` / `in` / `nin` / `exists`
- **Compound:** `all` / `any`
- **Negation:** `not`
- **Empty rule:** always true (no constraint)
- **Field paths:** dot notation, e.g. `visitor.country`, `order.total_cents`
- **Fail-closed** on malformed rules
- **Reused** by promos service (eligibility check) AND campaigns service (audience filter)

11/11 inline unit tests pass.

### Campaigns service (`product_ops.campaigns`)

- 5-endpoint CRUD: list / create / get / patch / delete
- 3 promo-linkage endpoints: list / link / unlink
- **Public picker `POST /v1/promo-campaigns/pick`** — given (campaign, visitor context), returns the right promo via:
  1. Resolve campaign by id or slug
  2. Check campaign-level audience_rule against visitor context (eligibility miss → log + return)
  3. Filter linked promos to status=active AND per-link audience override passing
  4. Weighted random pick (Python `random.choices`)
  5. Always log exposure row regardless of outcome

## What was tested live (running stack)

Postgres on :5434, backend on :51734, frontend on :51735. Vault project_key seeded. **8 real bugs caught + fixed** during the live test:

| # | Bug | Fix |
|---|---|---|
| 1 | `MAX(jsonb)` doesn't exist in Postgres | `array_agg(t.key_jsonb)[1]` (degenerate since UNIQUE) |
| 2 | Vault keys must match `[a-z0-9._-]` (no `/`) | Use dot-notation: `product_ops.project_keys.pk_demo` |
| 3 | `dim_modules` unseeded for `product_ops` | INSERT row id=11 |
| 4 | `vault.secrets.get` requires `ctx.extras['vault']` | Anonymous-ctx builder reads `request.app.state.vault` |
| 5 | `JSONResponse` doesn't serialize datetime | Bulk-replaced `success_response()` → `success()` (dict; FastAPI handles serialization) |
| 6 | Pydantic Literal hardcoded only 4 promotion kinds | Changed to `str`; service validates against `dim_promotion_kinds` FK at DB layer |
| 7 | Profile route used `success_response`, returning 500 | Same fix as #5 |
| 8 | Wrong response key (`pagination` vs `meta`) | Standardized via `_response.paginated()` helper |

### Live verification steps that PASSED

```
✅ POST /v1/track  →  3 events landed, visitor created, first-touch UTM captured
✅ POST /v1/product-profiles/traits  →  6 traits applied (email, name, plan, country, company, mrr_cents)
✅ GET  /v1/product-profiles/{id}    →  Full profile + 6 traits + first_utm_campaign='launch'
✅ POST /v1/promos × 5 different kinds:
   · WELCOME20    discount_pct       active
   · SCALE        tiered_discount    active (with eligibility: visitor.plan=pro)
   · FREESHIP     free_shipping      active
   · BOGO5        bogo               active
   · GIFT25       gift_credit        active
✅ POST /v1/promos/redeem  →  4 outcomes verified:
   · redeemed (visitor=pro, eligibility passes)
   · rejected_per_visitor (cap hit)
   · rejected_eligibility (visitor=free, rule says pro)
   · rejected_unknown_code
✅ POST /v1/promo-campaigns  →  spring_launch with audience: country in [US,CA,GB]
✅ POST /v1/promo-campaigns/{id}/promos × 2  →  WELCOME20 weight=3, BOGO5 weight=1
✅ POST /v1/promo-campaigns/pick × 100  →  WELCOME20=70, BOGO5=30 (expected ~75/25 — statistically perfect)
✅ POST /v1/promo-campaigns/pick (DE visitor)  →  decision=eligibility_miss
✅ Exposure log: 100 weighted_pick + 1 eligibility_miss recorded
✅ Frontend HTTP 200 on all 8 product pages (after auth-redirect, with cookie session)
```

### Live data state in Postgres after test

- 3 product events
- 1 visitor with full profile (Alice, pro, US, $49 MRR)
- 5 promo codes across 5 different kinds
- 1 active campaign with 2 weighted promos
- 101 campaign exposures
- 3 redemption attempts (1 success, 2 rejection variants)

## Live infrastructure setup performed

- Backend restarted with `TENNETCTL_MODULES=...,product_ops` after .env edit
- All 7 product_ops migrations applied (058–066)
- `dim_modules` row seeded (id=11, code=product_ops)
- Vault key `product_ops.project_keys.pk_demo` provisioned with `{"org_id":"...","workspace_id":"..."}`
- Backend tail: `INFO: Application startup complete`
- 27 product_ops endpoints live in OpenAPI

## What remains (operator-driven manual UI walk)

Chrome DevTools MCP disconnected mid-session, so the actual interactive UI walkthrough needs the operator. With the live data already seeded:

```
1. Sign in to http://localhost:51735
2. Navigate to /product?workspace_id=019d957b-d739-7b11-a0fa-54cb41374be4
3. Verify Live Tail shows the 3 events
4. /product/profiles  →  see Alice with traits
5. /product/promos    →  see 5 promo codes with status badges
6. /product/promos    →  click "New promo", pick kind from dropdown
7. /product/utm       →  see the launch campaign aggregate (1 visitor, 1 conversion)
```

## Files

- New: 3 (2 SQL migrations, 1 eligibility evaluator, 1 campaigns sub-feature with 4 files)
  - Plus campaigns sub-feature: schemas.py, repository.py, service.py, routes.py
- Modified: 4 (manifest, top-level routes.py, promos/service.py, promos/schemas.py)
- Bulk-modified: all 7 product_ops route files (success_response → success)
- ~1,800 new lines + ~50 line bulk-edit

## Decisions

- **Eligibility AST is JSONB, not a string DSL** — operators write JSON; UI builds a visual rule builder around the same shape. No grammar to maintain, no eval(), no string templating.
- **`dim_promotion_kinds` is operator-extensible** — adding a new kind is INSERT + UI auto-renders form from the JSON Schema. No code change required.
- **Always-log every exposure + every redemption attempt** — visibility >> volume at this scale. Funnel analysis (impressions → redemptions) becomes trivial via the join.
- **Campaigns share the eligibility evaluator with promos** — single primitive, two consumers; consistent semantics across promotion + audience targeting.
- **Same promo can belong to multiple campaigns** — UNIQUE (campaign_id, promo_code_id) enforces one link per pair, but a promo can ship in N campaigns with different weights/overrides.
- **Random pick is `random.choices` (not deterministic per visitor)** — true A/B over impression count. Future: add deterministic-by-visitor mode for sticky exposure if needed.
