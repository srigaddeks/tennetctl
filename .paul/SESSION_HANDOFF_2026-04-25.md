# Session handoff — 2026-04-25

End-of-session snapshot for the autonomous build run on `feat/saas-build`.

---

## What shipped this session

12+ commits, all on `feat/saas-build`, all pushed to origin:

| commit    | what                                                                  |
| --------- | --------------------------------------------------------------------- |
| `9cc529d` | product_ops feature — Mixpanel/OpenPanel-lite event tracking          |
| `abf8da1` | audit silent-drop fix + test infra repairs                            |
| `dac3df3` | browser SDK + auto page-view tracking on all frontends                |
| `7de5d12` | mobile-OTP via Twilio in tennetctl (vault-driven, every app reuses)   |
| `84f7516` | 7 standard ERP/CRM roles + 28 permissions + Outfit/Inter typography   |
| `eb005fb` | apps/somashop scaffold + greyscale palette across all frontends       |
| `6a7ac25` | real Soma Delights catalog + customer checkout flow + brand polish    |
| `179a172` | somashop profile + cart indicator + footer + E2E smoke script         |
| `5a525ee` | signin pages brand-aligned + stack map + handoff docs                 |
| `fe68ee0` | order detail page + RBAC enforcement (proof on contacts.create + recipes.create) |
| `c293082` | editorial home page — testimonials + how-it-works + FAQ               |
| (next)    | somashop README + handoff update                                      |

## Customer flow shipped end-to-end

The whole `Soma Delights customer journey` is wired and live:

1. Land on http://localhost:51741 — editorial home (hero, pull quote,
   3 pillars, 4-step how-it-works, 2 testimonials, 5-question FAQ, dark
   CTA strip).
2. Click "Start a free week" or "Sign in" → mobile-OTP signin
   (split-screen brand panel + form). Stub-mode echoes the OTP back
   in the response so dev flow works without Twilio.
3. Verify code → land on home as authenticated customer (name in topbar).
4. /products — 3 subscription plans + 10 real products
   (ABC Juice, Classic Green, Clarity Greens, Beet Boost, Amla Juice,
   Turmeric Glow, Immunity Shield, Digest Ease, Diabetes Care, BP Balance).
   Real prices in INR.
5. Click any product → detail page with target benefit + ingredients.
6. Click "Subscribe" on a plan → /checkout?plan=... cart pill appears in
   topbar, name pre-filled from auth, address form.
7. Submit → backend creates somaerp customer + subscription + emits
   audit event → redirect to /orders with success banner.
8. /orders shows the active subscription with status badge.
9. Click order → /orders/[id] detail page with cadence, price, started,
   service zone, delivery cadence card.
10. /profile shows account info, sign out.

## Stack state

All 4 backends + 4 frontends running locally on weird ports (see CREDS_DEV.md).
Postgres on `:5434`, single-tenant, vault root key in env.

```
:51734 tennetctl backend
:51735 tennetctl frontend
:51736 somaerp backend
:51737 somaerp frontend
:51738 somacrm backend
:51739 somacrm frontend
:51740 somashop backend
:51741 somashop frontend
```

## Verified live

End-to-end customer journey passes: `scripts/smoke_somashop_e2e.py`
exercises mobile-OTP → verify → list products → list plans → place order →
confirm subscription appears in `/v1/my-orders`. Run it any time.

55 pytests green (49 prior + 6 new mobile-OTP). Frontend typecheck clean
across all 4 apps.

## Catalog seeded

3 product lines, 10 real products, 3 subscription plans. Re-seed with
`scripts.seed_soma_catalog`. All idempotent.

## Brand cohesion

99_business_refs/website is the source of truth. All 4 frontends now load
Outfit/Inter/Lora and use the stone greyscale palette. Color is reserved
for status semantics + product photography.

## Carry-forward (next session)

### Customer experience
- Order detail page (`/orders/[id]`) — currently the orders list shows status
  but doesn't drill into delivery history.
- Self-serve subscription pause / cancel.
- Product photography slot — DB has the schema, no images uploaded yet.
- Razorpay (or similar) payment link — subscriptions are created without
  payment collection in v1.

### Twilio
- Provision real Twilio creds, POST into vault under
  `sms.twilio.{account_sid, auth_token, from_number}`. Sender flips from
  stub to live within 60 seconds (vault TTL). No code change.

### RBAC
- 7 standard roles exist. Endpoints don't enforce them yet —
  `require_permission(...)` is the next mile. Pick somacrm.contacts.create
  as the first one and template the rest.

### Per-page brand polish
- somaerp + somacrm dashboards are clean. List + detail pages still use
  card-heavy patterns from the blue-accent era. A pass on the table /
  filter chrome would make them as editorial as the customer app.

### Tests
- `tests/conftest.py` admin-session fixture warns about partition_manager
  CancelledError on teardown (pre-existing). Wrap the cancel in `try /
  except CancelledError` to silence.

### Docs
- Per-app README under `apps/somashop/` (currently has none).
- ADR for "service-account session model for cross-app reads" — somashop
  signs in at boot to query somaerp because somaerp accepts only session
  tokens, not API keys. Document the decision so future devs don't try to
  swap to API-key auth.

---

## Recent context links

- Brand spec: `99_business_refs/website/.planning/REQUIREMENTS.md`
- Audit handoff (last session): `.paul/AUDIT_HANDOFF_2026-04-20.md`
- Recipes seeded from: `99_business_refs/website/docs/recipes/*.md`
