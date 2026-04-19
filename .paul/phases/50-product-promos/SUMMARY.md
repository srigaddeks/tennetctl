# Phase 50 — Promo Codes — SUMMARY

**Status:** APPLY complete.
**Date:** 2026-04-19

## Schema (NNN=063)

- `10_fct_promo_codes` — code + redemption_kind (typed: discount_pct / discount_cents / free_trial_days / custom) + redemption_config JSONB + usage caps (max_total + max_per_visitor) + time window (starts_at / ends_at) + eligibility JSONB. UNIQUE per (workspace, code). CHECK on redemption_kind enum.
- `60_evt_promo_redemptions` — append-only attempt log (one row per redeem call: success OR rejection). Outcome enum: redeemed / rejected_max_uses / rejected_per_visitor / rejected_expired / rejected_inactive / rejected_eligibility / rejected_unknown_code.
- `v_promo_codes` view — pre-aggregated redemption_count + rejection_count + computed status (scheduled / active / expired / inactive / exhausted).

## Backend sub-feature `product_ops.promos`

- schemas.py — CreatePromoCodeBody, UpdatePromoCodeBody, RedeemPromoBody, RedeemPromoResponse, PromoCodeOut
- repository.py — insert/get/list/update/soft_delete + count_redemptions_for_visitor + insert_redemption
- service.py — create_code, update_code, delete_code, **redeem** (the heart: status checks + per-visitor cap + always-write redemption row + audit per attempt)
- routes.py — full 5-endpoint admin CRUD + public POST /v1/promos/redeem

## Distinction from Phase 47 Referrals (documented in schema header)

- **Promos** discount the redeemer (coupons). Track per-visitor caps, expiry, eligibility.
- **Referrals** credit the referrer (affiliate-style). Track conversions, reward config per code.

Same code-string concept but different consumers, different storage, different metrics.

## Frontend

- types/api.ts: PromoCode, PromoListResponse, CreatePromoBody, RedeemPromoResponse, PromoStatus, PromoRedemptionKind
- features/product-ops/hooks/use-promos.ts: list/create/delete TanStack hooks
- app/(dashboard)/product/promos/page.tsx: list with status filter + pre-aggregated counts + status badges; inline create form with kind-aware value input (discount_pct / discount_cents / free_trial_days / custom JSON)
- Sidebar entry `/product/promos`

## Verification

- All 5 module imports clean ✅
- Manifest validates: 5 sub-features, 27 routes ✅
- Frontend typecheck clean ✅
- Live integration deferred to operator

## Files

- New: 7 (1 SQL, 4 backend, 1 hook, 1 page)
- Modified: 4 (manifest, top-level routes.py, types/api.ts, features.ts)
- ~1,200 new lines

## Key decisions

- **Always-log every redemption attempt** (even rejections) for fraud forensics. Phase 13 monitoring precedent: high-value events stay first-class even when rejected.
- **Computed `status` lives in the view**, not on the table. Lets operators reason about state without service-layer recomputation; index-friendly.
- **`eligibility` JSONB is opaque to v1 service** — operator enforces externally. v2 may interpret common shapes ({"plan":"free"}, etc.).
- **CHECK constraint on outcome enum** + Pydantic Literal — triple defense like the audit category contract.
