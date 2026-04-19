# Phase 51 — Partner Management — SUMMARY

**Status:** APPLY complete.
**Date:** 2026-04-19
**Reference shape:** dib.co-style B2B affiliate platform.

## Schema (NNN=064)

- `01_dim_partner_tiers` — 4 seeded tiers (standard 10% / silver 15% / gold 20% / platinum 25%); `default_payout_bp` in basis points.
- `10_fct_partners` — slug + display_name + contact_email + tier_id (FK) + optional user_id (IAM binding for partner login). UNIQUE per (workspace, slug).
- `40_lnk_partner_codes` — discriminated-union linkage. CHECK enforces exactly one of (referral_code_id, promo_code_id) is set per row, matching code_kind. Per-link payout_bp_override allows partner-specific deals.
- `60_evt_partner_payouts` — append-only payout log with status enum (pending / paid / failed / cancelled), period window, external_ref for upstream financial-system reconciliation (Stripe payout id, etc.).
- `v_partners` view — pre-aggregated stats: code_count, conversion_count + conversion_value_cents_total (joined through Phase 47 referrals), payout_paid_cents + payout_pending_cents.

## Backend sub-feature `product_ops.partners`

- schemas.py — CreatePartnerBody (slug regex), UpdatePartnerBody, LinkCodeBody (discriminated union), CreatePayoutBody, PartnerOut
- repository.py — partner CRUD + link/unlink + insert_payout + list_payouts
- service.py — create_partner (slug-collision 409), update_partner, delete_partner, link_code_to_partner (validates discriminated union shape), record_payout
- routes.py — 10 routes:
  - 5-endpoint partner CRUD
  - 3 code-linkage routes (list/link/unlink)
  - 2 payout routes (list/record)

## Frontend

- types/api.ts: Partner, CreatePartnerBody, PartnerCodeLink, PartnerPayout (+ list responses)
- features/product-ops/hooks/use-partners.ts: usePartners, usePartner, usePartnerCodes, usePartnerPayouts, useCreatePartner, useDeletePartner
- app/(dashboard)/product/partners/page.tsx: tier-filtered partner table with pre-aggregated payout stats (paid + pending columns), tier badges color-coded by tier, inline create form
- Sidebar entry `/product/partners`
- Currency rendered via `Intl.NumberFormat` (USD default)

## Verification

- All 5 module imports clean ✅
- Manifest validates: 6 sub-features, 37 routes ✅
- Frontend typecheck clean ✅
- EmailStr (pydantic[email-validator]) confirmed available ✅
- Live integration deferred to operator

## Files

- New: 7 (1 SQL, 4 backend, 1 hook, 1 page)
- Modified: 4 (manifest, top-level routes.py, types/api.ts, features.ts)
- ~1,400 new lines

## How this composes the platform

```
Partner (acme-agency, gold tier, 20% default)
  ├─ owns referral code "acme20"  (Phase 47) → conversions + value flow into v_partners
  ├─ owns referral code "acme-launch"
  ├─ owns promo code "ACME10" (Phase 50, 10% off, max 1000 uses) — promotion the partner runs
  └─ payouts logged with external_ref = stripe_po_… (operator pushes to Stripe, records here)
```

Acquisition flow per visitor:
1. Visitor lands with `?ref=acme20` → Phase 47 attaches referral → utm_source=referral / utm_campaign=acme20 touch lands in Phase 45 stream
2. Visitor signs up → Phase 47 records referral conversion
3. Phase 51's v_partners view aggregates that conversion into Acme's stats
4. Operator runs monthly: queries v_partners.payout_pending_cents, records payout, pushes to Stripe, records external_ref

## Deferred

- **Partner-facing dashboard** — current admin UI is operator-side. Partner login route (using existing IAM `user_id` binding) + partner-only API surface is a 51-x follow-up.
- **Auto-payout calculation** — current model is operator-records-amount. A scheduled service that computes pending payout from the last paid_at + tier rate + linked-code conversions could land in v0.7.
- **Tier auto-promotion** — based on lifetime conversion value crossing thresholds. Defer to v0.7.
