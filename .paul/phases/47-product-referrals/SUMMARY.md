# Phase 47 — Referrals — SUMMARY

**Status:** APPLY complete.
**Date:** 2026-04-19

## Schema (NNN=061)

- `10_fct_referral_codes` — code + referrer_user_id + reward_config JSONB. UNIQUE per (workspace, code).
- `60_evt_referral_conversions` — append-only conversion log; FK to fct_referral_codes; conversion_kind (signup/purchase/caller-defined) + value_cents.
- `v_referral_codes` view — exposes code + pre-aggregated conversion_count + conversion_value_cents_total.

## Backend sub-feature `product_ops.referrals`

- schemas.py — CreateReferralCodeBody, AttachReferralBody, RecordConversionBody, ReferralCodeOut
- repository.py — insert/get-by-id/get-by-code/list/soft_delete/insert_conversion
- service.py — create_code, attach_referral, record_conversion (audit emitted via run_node)
- routes.py — list/create/get/delete + POST /v1/referrals/attach + POST /v1/referrals/conversions
- nodes/attach.py — `product_ops.referrals.attach` (effect, tx=own, emits audit)

## Integration with Phase 45 event stream

`attach_referral` writes a synthetic touch row with `utm_source='referral'` and `utm_campaign={code}` directly into evt_attribution_touches, plus a `referral_attached` event into evt_product_events. Result: referrals show up in the standard UTM dashboard (Phase 45-03) with no special-case UI — closes the loop on the CONTEXT.md decision.

## Frontend

- types/api.ts: ReferralCode, ReferralListResponse, CreateReferralBody
- features/product-ops/hooks/use-referrals.ts: list/create/delete TanStack hooks
- app/(dashboard)/product/referrals/page.tsx: list with conversion stats + inline create form
- Sidebar entry `/product/referrals`

## Verification

- Backend imports clean ✅
- Manifest validates (3 sub-features: events, links, referrals) ✅
- Frontend typecheck clean ✅
- Live integration deferred to operator

## Files

- New: 7 (1 SQL, 5 backend, 2 frontend)
- Modified: 4 (manifest, top-level routes.py, types/api.ts, features.ts)
- ~1,000 new lines
