# somaerp — Overview

**Status:** Foundation (Phase 56, v0.9.0)
**Date:** 2026-04-24
**Position in monorepo:** `apps/somaerp/` — sibling to `apps/solsocial/`, consumer of `tennetctl/` primitives.

## Mission

A self-hostable, generic, multi-kitchen, multi-region ERP for product businesses. somaerp models the universal shape of a small-batch production business — locations, kitchens, capacity, products, recipes, raw materials, suppliers, procurement, production batches, quality control, customers, subscriptions, delivery routes, delivery runs — and lets each tenant configure that shape to their reality without forking the codebase.

First tenant: **Soma Delights** — a Hyderabad cold-pressed juice subscription business operating at the home-kitchen stage with FSSAI compliance pressure. somaerp v0.9.0 is shaped by what Soma Delights needs at 4 AM with juice on its operator's hands; subsequent tenants validate the genericity.

## In scope (v0.9.0)

- Geography: regions → locations → kitchens → service zones → time-windowed capacity per (kitchen × product line)
- Catalog: product lines → products → variants
- Recipes: versioned recipes with ingredients and steps; per-kitchen overrides
- Quality: multi-stage QC checkpoints + immutable check event log; photos via tennetctl vault
- Raw materials and suppliers: lot-tracked materials, multi-source suppliers
- Procurement: append-only procurement runs + inventory movements + computed current-inventory view
- Production batches: state-machine lifecycle (planned → in_progress → completed | cancelled), recipe-version-pinned, ingredient consumption + step logs + QC results
- Customers and subscriptions: customer records, plan templates, subscription state, pause history
- Delivery: routes, route-customer mapping, delivery runs with stop-level evidence
- Per-tenant `properties JSONB` extension column on every `fct_*` for tenant-specific fields without schema changes

## Explicitly out of scope (v0.9.0)

- Metered billing engine (deferred until somacrm forces the question; payments stored as records)
- HR / shift management, equipment maintenance, allergen labeling computation (deferred to v0.10+)
- Offline-tolerant data entry with sync (deferred to v1.0)
- Visual workflow editor inside somaerp (use tennetctl flows when needed)
- somacrm — separate phase, separate app
- Any external SaaS dependency for payments, email, SMS, billing, or notifications — empire thesis prohibits

## Reading order

1. `00_main/00_overview.md` (this file) — what somaerp is
2. `00_main/01_architecture.md` — how it sits on the tennetctl backbone, layered breakdown, hybrid data approach
3. `00_main/02_tenant_model.md` — what a tenant is, how isolation works, audit scope
4. `00_main/08_decisions/001` through `008` — the eight foundational ADRs (read in order)
5. `04_integration/00_tennetctl_proxy_pattern.md` — how somaerp talks to tennetctl
6. `01_data_model/*` — schema layer specs (10 docs)
7. `02_api_design/*` — REST surface specs (10 docs)
8. `03_scaling/*` — multi-tenant, multi-region, capacity, residency strategy (4 docs)
9. `04_integration/01..05` — primitive-by-primitive integration deep dives (5 docs)
10. `05_tenants/01_somadelights_tenant_config.md` — first-tenant configuration map

## Parent design doc

The architectural premises captured here originated in the office-hours design session of 2026-04-24:

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`

The aspirational original ERP plan that drove the hardcoded-skeleton-plus-properties-JSONB hybrid approach:

- `99_business_refs/somadelights/09-execution/erp-system-plan.md`

The proven thin-app-on-tennetctl precedent that somaerp follows:

- `apps/solsocial/README.md`
- `apps/solsocial/backend/01_core/tennetctl_client.py`
