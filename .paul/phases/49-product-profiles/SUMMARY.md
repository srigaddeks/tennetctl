# Phase 49 — Profiles & Traits — SUMMARY

**Status:** APPLY complete.
**Date:** 2026-04-19

## Schema (NNN=062)

- `20_dtl_visitor_attrs` — EAV trait storage (one row per visitor × attr_def). UNIQUE on (visitor_id, attr_def_id) → INSERT … ON CONFLICT DO UPDATE = last-write-wins. Triple-CHECK that exactly one of key_text/key_jsonb/key_smallint is set (matches IAM/audit dtl pattern).
- 10 seeded `dim_attr_defs` rows for canonical traits: email, phone, name, plan, mrr_cents, country, company, role, signup_at, last_login_at.
- `v_visitor_profiles` view — pivots EAV via MAX(...) FILTER pattern (Phase 3 + 45 precedent).

## Backend sub-feature `product_ops.profiles`

- schemas.py — SetTraitsBody, ProfileOut, TraitOut, ProfileListResponse
- repository.py — get_attr_defs, upsert_visitor_attr, get_visitor_attrs, get_profile, list_profiles (with q/plan/country filters)
- service.py — set_traits (resolves visitor_id from anonymous_id; drops unknown traits with skipped report; one audit per call), get_profile_full (joins pivot + raw trait list)
- routes.py — GET /v1/product-profiles (list with filters), POST /v1/product-profiles/traits, GET /v1/product-profiles/{visitor_id}

## Frontend

- types/api.ts: ProductProfile, ProductProfileTrait, ProductProfileListResponse
- features/product-ops/hooks/use-profiles.ts: useProfiles, useProfile
- app/(dashboard)/product/profiles/page.tsx: filterable list (search + plan + country) with click-through to visitor detail
- Sidebar entry `/product/profiles`

## Verification

- All 4 module imports clean ✅
- Manifest validates: 4 sub-features, 21 routes ✅
- Frontend typecheck clean ✅
- Live integration deferred to operator

## Files

- New: 5 (1 SQL, 4 backend, 1 hook, 1 page)
- Modified: 4 (manifest, routes.py, types/api.ts, features.ts)
- ~900 new lines

## Key decisions

- **Last-write-wins on traits** via UNIQUE + ON CONFLICT DO UPDATE. Audit trail of trait changes lives in `evt_audit` (`product_ops.profiles.traits_set` summary per call). If per-trait history is needed later, add an evt_visitor_trait_changes log without touching dtl_visitor_attrs.
- **Unknown trait codes silently dropped** (returned in `skipped[]`). Operators register new traits via dim_attr_defs first. This forces taxonomy discipline.
- **First-touch attribution flows through** the v_visitor_profiles view (inherited from fct_visitors columns) so a single profile read shows both traits + acquisition source.
