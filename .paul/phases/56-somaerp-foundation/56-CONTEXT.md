# Phase 56 — somaerp Foundation

**Milestone:** v0.9.0 — somaerp Foundation
**Started:** 2026-04-24
**Status:** Planning

## What this phase delivers

`apps/somaerp` — a generic, multi-kitchen, multi-region ERP application that sits on the tennetctl backbone. First tenant: Soma Delights (Hyderabad cold-pressed juice subscription). Architected from day one to scale to multiple tenants in multiple geographies running multiple kitchens producing the same or different recipes.

## Why now

- v0.8.0 GDPR DSAR shipped 2026-04-23. tennetctl has the full primitive set required (auth, IAM, audit, vault, notify, flows, billing-stub) for thin business apps.
- `apps/solsocial` proves the "thin app on tennetctl primitives" pattern works in production.
- Soma Delights has real, FSSAI-mandated ops pain (daily 4 AM batch logs, milkman delivery routes, multi-source procurement) that needs production software, not spreadsheets.
- User's stated thesis: **tennetctl is the OS for self-hosted business SaaS apps; somaerp + somacrm + future apps are thin shells consuming tennetctl primitives.** No external SaaS dependencies, ever.

## Architectural premises (confirmed during /office-hours 2026-04-24)

1. **tennetctl backbone** — auth/IAM/audit/vault/notify/flows/billing all consumed via the `tennetctl_client.py` proxy pattern (solsocial precedent). No reimplementation in somaerp.
2. **Hybrid data model** — opinionated hardcoded ERP skeleton (locations, kitchens, products, recipes, batches, QC, raw materials, suppliers, customers, subscriptions, deliveries) PLUS `properties JSONB` extension column on every fct_* table for tenant-specific custom fields. Reference: `99_business_refs/somadelights/09-execution/erp-system-plan.md`.
3. **Multi-tenant by default** — every fct_* row carries `tenant_id` (= tennetctl workspace_id). Single-tenant deployments use the bootstrap workspace.
4. **Multi-kitchen, multi-region from day 1** — capacity model, recipe-per-kitchen overrides, route-to-kitchen mapping, time-zone awareness, multi-currency pricing all baked into v0.1 schema. Performance carve-outs (e.g. hot-path indexes on production_batches.run_date + kitchen_id) allowed where indexed query performance demands it.
5. **Vertical feature slices** — every plan after 56-01 ships paired backend + frontend, demoed end-to-end, before the next plan begins. NEVER backend-first.
6. **Soma Delights = first tenant config** — the somaerp schema is universal; Soma Delights workflows are seeded as a tenant configuration (entity instances, recipes, routes), not as schema.

## Plans in this phase

**Resequenced 2026-04-24 during 56-03 plan-time:** capacity moved from 56-03 → 56-06 because `fct_kitchen_capacity` references `fct_product_lines` (catalog, 56-04) and `dim_units_of_measure` (raw materials, 56-05). Phase 56 grew from 12 to 13 plans. The clean dependency graph beats the "fewer plans" optimization.

| Plan | Concern | Status |
|---|---|---|
| **56-01** | Documentation Suite (zero code) | ✓ Complete (UNIFIED 2026-04-24) |
| **56-02** | Base infrastructure — apps/somaerp scaffold + 00_health proxy + Next.js shell | ✓ Complete (UNIFIED 2026-04-24) |
| **56-03** | Geography MINUS capacity — regions + locations + kitchens + service zones + admin UI | PLAN created 2026-04-24 |
| 56-04 | Catalog vertical — product lines, products, variants + admin UI | Not drafted |
| 56-05 | Raw Materials core — units_of_measure + raw_materials + suppliers (catalog of inputs) | Not drafted |
| 56-06 | Kitchen Capacity — fct_kitchen_capacity + admin UI (deps now exist: product_lines + units) | Not drafted |
| 56-07 | Recipes vertical — recipes, versions, ingredients, steps, kitchen overrides | Not drafted |
| 56-08 | Quality Control vertical — checkpoints, criteria, evt_qc_checks | Not drafted |
| 56-09 | Procurement + Inventory vertical | Not drafted |
| 56-10 | Production Batches vertical (THE driving workflow) — mobile-first 4 AM tracker | Not drafted |
| 56-11 | Customers + Subscriptions vertical | Not drafted |
| 56-12 | Delivery Routes + Runs vertical — rider mobile UI | Not drafted |
| 56-13 | Reporting Views — yield, COGS, spoilage, FSSAI compliance | Not drafted |

## Reference materials

- Office-hours design doc: `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- Soma Delights strategy + ops: `99_business_refs/somadelights/` (10 numbered top-level dirs)
- Pre-written ERP plan (aspirational, not v0.1 scope): `99_business_refs/somadelights/09-execution/erp-system-plan.md`
- Solsocial precedent (thin-app pattern): `apps/solsocial/README.md`
- tennetctl conventions: `CLAUDE.md` (root) + `.claude/rules/common/core.md`

## Tenant boundary decision (canonical here, formalized in ADR-001)

- **tennetctl org** = the platform owner (SRI's organization running this self-hosted instance)
- **tennetctl workspace** = a customer of the platform (Soma Delights = workspace #1)
- **somaerp tenant_id** = the tennetctl workspace_id (no new tenant table; reuse IAM)
- IAM/RBAC scoped at workspace level via existing tennetctl 03_iam primitives
- Audit emission carries (user_id, session_id, org_id, workspace_id) per existing audit-scope mandate

## Scaling stance

- v0.1 ships single-Postgres single-region but the schema/IDs are shard-friendly: UUID v7 PKs (already project convention), tenant_id on every row (natural shard key), UTC timestamps, currency code on monetary columns, multi-currency pricing tables ready.
- Multi-region read replicas + tenant sharding deferred to v1.0+ but documented now in the scaling strategy doc.

## Out of scope for v0.9.0

- Lago-style metered billing engine (deferred — payments stored as records; build the real billing primitive when somacrm needs it)
- HR / shift management (defer to v0.10)
- Equipment maintenance tracking (defer to v0.10)
- Allergen / nutrition labeling computation (defer)
- Offline-tolerant data entry with sync (defer to v1.0)
- somacrm (separate phase, v0.10+)
- Visual workflow editor inside somaerp (use tennetctl flows when needed)
