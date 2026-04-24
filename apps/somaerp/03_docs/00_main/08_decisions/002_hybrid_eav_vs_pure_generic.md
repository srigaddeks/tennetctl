# ADR-002: Hybrid hardcoded skeleton + properties JSONB (NOT pure generic EAV)
Status: ACCEPTED
Date: 2026-04-24

## Context

The original aspirational ERP plan (`99_business_refs/somadelights/09-execution/erp-system-plan.md`) proposed a hardcoded ERP skeleton with a `properties JSONB` extension column on every entity. The office-hours session of 2026-04-24 first overshot toward a pure-generic-EAV framework (entity_type_definitions + field_definitions + entity instances with all-attrs-in-JSONB) and then walked back to the original hybrid approach. This ADR records the walked-back position as the binding decision for somaerp v0.9.0. Getting this wrong forces every hot-path query (today's batches at this kitchen, current inventory by raw material, weekly yield by SKU) into a JSONB join graph and breaks index economics. The project also has a long-standing pure-EAV rule (no business columns on `fct_*`) that this decision must explicitly except.

## Decision

**somaerp uses a hybrid data model: real `fct_*` tables with real columns for the universal ERP skeleton (locations, kitchens, capacity, products, recipes, raw materials, suppliers, procurement runs, production batches, QC checks, customers, subscriptions, delivery routes, delivery runs), PLUS a `properties JSONB NOT NULL DEFAULT '{}'` extension column on every `fct_*` table for tenant-specific custom fields.** This is a documented exception to the project's pure-EAV rule, scoped to the somaerp app layer only. Tenant-specific fields live in `properties`. When a `properties` field becomes universal (used by 3+ tenants with the same semantics), it is promoted to a real column in a future migration. somaerp does NOT ship a generic `entity_type_definitions` framework, does NOT ship configurable fields per tenant via UI, and does NOT model recipes/batches/etc. as generic entities.

## Consequences

- **Easier:** hot-path queries hit real indexed columns. Reading "today's production batches at KPHB Kitchen for Cold-Pressed Drinks" is a B-tree index lookup, not a JSONB scan.
- **Easier:** Pydantic schemas are concrete; API contracts are typed; frontend forms are auto-generatable from schema; FSSAI-relevant columns (lot numbers, batch IDs, QC pass/fail) are first-class.
- **Easier:** every tenant gets an extension surface (`properties JSONB`) without schema migrations. Soma Delights can store their own custom fields (e.g. `bottle_color`, `label_batch_code`) without forking the codebase.
- **Harder:** new universal fields require a real schema migration, not a UI configuration change.
- **Harder:** the project's pure-EAV rule has now grown a second documented exception (after monitoring `fct_*`). Future apps must explicitly opt in to one or the other.
- **Constrains:** ADR-007 (production batch lifecycle uses real state machine columns); ADR-006 (inventory uses real procurement_runs and inventory_movements tables); ADR-005 (QC uses real evt_qc_checks); all data model layer specs in `01_data_model/*` must include `properties JSONB` on every `fct_*`.

## Alternatives Considered

- **Pure generic EAV (`entity_type_definitions` + `field_definitions` + `attrs JSONB` on a single `fct_eav_entities` table).** Maximum flexibility, zero schema work for new entity shapes. Rejected during office hours: forces every hot-path query into JSONB joins, makes Pydantic schemas dynamic and untypable, makes FSSAI-relevant columns indistinguishable from custom fields, and the user explicitly walked this back.
- **Pure pure-EAV (no JSONB extension at all, all attrs in `dtl_attrs` rows).** Most disciplined, matches tennetctl primitive convention. Rejected: blows up row counts (a single batch with 30 attributes = 30 dtl rows), and somaerp is an app layer where the extension is the entire point of `properties JSONB`.
- **Hardcoded only, no extension.** Cleanest schema. Rejected: forces every tenant-specific custom field into a code change; defeats the multi-tenant generic-product thesis.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/09-execution/erp-system-plan.md`
- `.claude/rules/common/database.md` (pure-EAV rule and exception precedent)
- Memory: `feedback_pure_eav_rule.md`, `project_somaerp_generic_eav.md`
- `apps/somaerp/03_docs/00_main/01_architecture.md`
