# Audit Emission

> Every somaerp mutation emits a tennetctl audit event with the mandatory four-tuple scope. No exceptions outside the two documented bypasses.

## The mandatory four-tuple (project-wide rule)

Per the project's `feedback_audit_scope_mandatory` rule, every audit event carries:

- `user_id` — the acting user (from session)
- `session_id` — the active session (from session)
- `org_id` — the platform owner org (from session)
- `workspace_id` — the somaerp tenant_id (from session)

A CHECK constraint at the tennetctl audit ingest layer enforces non-NULL on this four-tuple. The somaerp service layer enforces it before calling `client.emit_audit(...)` — a missing field raises before the mutation commits.

## How somaerp emits

Per `00_tennetctl_proxy_pattern.md`, every service-layer mutation calls:

```text
await client.emit_audit(
    event_key="somaerp.{layer}.{entity}.{action}",   # e.g. "somaerp.production.batches.created"
    outcome="success",                                # or "failure"
    metadata={                                        # event-specific structured payload
        "entity_id": str(entity_id),
        "category": "operational",                    # or "compliance" / "privacy" / "critical" / "setup" / "system"
        ...
    },
    actor_user_id=request.state.user_id,
    org_id=request.state.org_id,
    workspace_id=request.state.workspace_id,
)
```

`session_id` is propagated through the service-API-key header chain by tennetctl's audit ingest middleware; somaerp does not pass it explicitly. Per `00_tennetctl_proxy_pattern.md`.

## Event key namespace — `somaerp.{layer}.{entity}.{action}`

Every key is namespaced under `somaerp.` (the application code). `{layer}` matches the data-model directory name (`geography`, `catalog`, `recipes`, `quality`, `raw_materials`, `procurement`, `production`, `customers`, `delivery`). `{entity}` is the table-or-collection (singular noun in plural form for collections, singular for singletons). `{action}` is one of `created` / `updated` / `deleted` / `state_changed` (state machine transitions) / a domain-specific verb where helpful.

### Event keys per layer

Cross-references the data_model docs (Task 2) — every fct_/evt_ table that accepts mutations declares one or more keys:

#### Geography (cross-references `01_data_model/01_geography.md`)
- `somaerp.geography.regions.created` / `.updated` / `.deleted`
- `somaerp.geography.locations.created` / `.updated` / `.deleted`
- `somaerp.geography.kitchens.created` / `.updated` / `.deleted`
- `somaerp.geography.kitchen_capacity.changed` (state-history mutation per ADR-003 two-step)
- `somaerp.geography.service_zones.created` / `.updated` / `.deleted`

#### Catalog (cross-references `01_data_model/02_catalog.md`)
- `somaerp.catalog.product_lines.created` / `.updated` / `.deleted`
- `somaerp.catalog.products.created` / `.updated` / `.deleted`
- `somaerp.catalog.product_variants.created` / `.updated` / `.deleted`

#### Recipes (cross-references `01_data_model/03_recipes.md`)
- `somaerp.recipes.created` (status=draft)
- `somaerp.recipes.activated` (draft→active, demotes prior active to archived per ADR-004)
- `somaerp.recipes.archived`
- `somaerp.recipes.kitchen_overrides.set` / `.cleared`

#### Quality (cross-references `01_data_model/04_quality.md`)
- `somaerp.quality.checkpoints.created` / `.updated` / `.deleted`
- `somaerp.quality.checks.recorded` (immutable per ADR-005, category=`compliance`)
- `somaerp.quality.checks.corrected` (insert corrective row, never edit)

#### Raw materials (cross-references `01_data_model/05_raw_materials.md`)
- `somaerp.raw_materials.created` / `.updated` / `.deleted`
- `somaerp.raw_materials.suppliers.created` / `.updated` / `.deleted`
- `somaerp.raw_materials.supplier_links.set` / `.cleared`

#### Procurement (cross-references `01_data_model/06_procurement.md`)
- `somaerp.procurement.runs.created` (immutable per ADR-006)
- `somaerp.procurement.movements.recorded` (every inventory movement, category=`compliance` for FSSAI)
- `somaerp.procurement.movements.adjusted` (correction movement)

#### Production (cross-references `01_data_model/07_production.md`)
- `somaerp.production.batches.created` (status=planned)
- `somaerp.production.batches.started` (state→in_progress)
- `somaerp.production.batches.completed` (state→completed)
- `somaerp.production.batches.cancelled` (state→cancelled)
- `somaerp.production.batches.qc_failed` (state→qc_failed substate per ADR-007)
- `somaerp.production.batch_steps.logged`
- `somaerp.production.batch_consumption.logged` (also emits an `evt_inventory_movement`)

#### Customers (cross-references `01_data_model/08_customers.md`)
- `somaerp.customers.created` / `.updated` / `.deleted`
- `somaerp.customers.subscriptions.created`
- `somaerp.customers.subscriptions.state_changed` (active / paused / cancelled)
- `somaerp.customers.subscriptions.paused` (insert into `evt_subscription_pauses`)
- `somaerp.customers.consent.recorded` (category=`privacy`)
- `somaerp.customers.dsar.exported` / `.dsar.deleted` (category=`privacy`)

#### Delivery (cross-references `01_data_model/09_delivery.md`)
- `somaerp.delivery.routes.created` / `.updated` / `.deleted`
- `somaerp.delivery.route_customers.added` / `.removed`
- `somaerp.delivery.runs.dispatched` (state→in_progress)
- `somaerp.delivery.runs.completed` (state→completed)
- `somaerp.delivery.stops.recorded` (per stop event with photo_vault_key)
- `somaerp.delivery.stops.failed` (category=`critical` if cold-chain breach)

## Audit categories

Categories are stamped in `metadata.category`. They drive retention and filtering:

| Category | Used for | Retention |
| --- | --- | --- |
| `operational` | Default — most mutations | Standard tennetctl audit retention |
| `compliance` | FSSAI-relevant: QC checks, lot consumption, batch completion | Extended (FSSAI demands ≥ 2 years) |
| `privacy` | DPDP-relevant: consent capture, DSAR, customer deletion | Extended (DPDP minimum) |
| `critical` | Operator-blocking: QC failure, cold-chain breach, FSSAI license breach | Highest retention; flagged for alerts |
| `setup` | First-tenant bootstrap; bypasses user_id requirement | Standard |
| `system` | Worker / scheduled task with no user actor; bypasses user_id requirement | Standard |

## The two documented bypasses

### Setup-mode bypass (no user_id required)

When somaerp seeds a fresh tenant config (Soma Delights bootstrap from `../05_tenants/01_somadelights_tenant_config.md`), no iam user has been created in that workspace yet. The setup-mode audit emission is allowed:

```text
await client.emit_audit(
    event_key="somaerp.geography.kitchens.created",
    outcome="success",
    metadata={"category": "setup", "entity_id": str(kitchen_id), ...},
    actor_user_id=None,                    # explicitly None — allowed only with category=setup
    org_id=PLATFORM_ORG_ID,
    workspace_id=tenant_workspace_id,
)
```

This bypass is enforced at the tennetctl audit ingest layer: `actor_user_id IS NULL` is only allowed when `metadata->>'category' = 'setup'`. Per `feedback_audit_scope_mandatory` memory.

### Failure-outcome bypass (partial scope allowed)

When a mutation fails before authentication completes (e.g. an invalid token, a malformed request that never reached the handler), the audit emission carries `outcome=failure` and may carry partial scope. Per `00_tennetctl_proxy_pattern.md`. This bypass is for visibility into pre-auth failures only; post-auth failures still carry full scope.

## Audit emission is best-effort, never blocking

Per `00_tennetctl_proxy_pattern.md`, `emit_audit` failures are swallowed and logged at WARN. Audit reliability is tennetctl's responsibility (queueing, retry, durable storage). somaerp never blocks a business mutation because the audit hop failed. This is the right tradeoff: one missed audit row is a tennetctl reliability fix; a blocked production batch is a Soma Delights revenue hit.

## Failure-mode emission (success path AND failure path both audited)

Every service-layer mutation emits exactly once:

- on success: `outcome="success"` with full scope and `metadata.entity_id`
- on caught exception: `outcome="failure"` with whatever scope was available, `metadata.error_code`, `metadata.error_message`

The success/failure split lives in the service layer, not the route layer. This guarantees an audit row exists for every attempted mutation, not just successful ones.

## Compliance auditor query examples

A FSSAI inspector visiting Soma Delights wants the QC + lot-consumption history for a date range:

```text
SELECT *
  FROM tennetctl.audit_events
 WHERE workspace_id = $soma_delights_workspace_id
   AND metadata->>'category' = 'compliance'
   AND created_at BETWEEN '2026-04-01' AND '2026-04-30'
 ORDER BY created_at
```

A DPDP investigator wants the privacy chain for one customer:

```text
SELECT *
  FROM tennetctl.audit_events
 WHERE workspace_id = $soma_delights_workspace_id
   AND metadata->>'category' = 'privacy'
   AND metadata->>'entity_id' = $customer_id::text
 ORDER BY created_at
```

Both queries are tennetctl-side; somaerp emits, tennetctl owns retention and query.

## NCP v1 § 9 reference

This emission model implements the National Compliance Profile § 9 audit-emission discipline: every mutation stamps the four-tuple, every category is declared, every bypass is named, every failure path is recorded.

## Related documents

- `00_tennetctl_proxy_pattern.md` — `emit_audit` signature and best-effort guarantee
- `01_auth_iam_consumption.md` — where the four-tuple comes from
- `03_vault_for_secrets_and_blobs.md` — vault read/write also emits audit
- `../05_tenants/01_somadelights_tenant_config.md` — setup-mode bootstrap audits
- `../00_main/08_decisions/005_qc_checkpoint_model.md` — compliance audit on QC
- `../00_main/08_decisions/006_inventory_and_procurement_model.md` — compliance audit on movements
- Memory: `feedback_audit_scope_mandatory.md`
