# Data Residency and Compliance

> Where customer data lives, why, and how somaerp + tennetctl primitives enforce regulatory obligations without app-layer special cases.

## v0.9.0 stance: residency by deployment topology, not by app code

somaerp v0.9.0 ships as one Postgres + one FastAPI process group. Per ADR-001 every row carries a `tenant_id` that maps to a tennetctl workspace. Data residency is enforced by **where the operator deploys the cluster**, not by per-row classification inside the app.

For Soma Delights this is straightforward:

- Soma Delights is a Hyderabad business serving Hyderabad customers under Indian law (DPDP Act 2023, FSSAI).
- The Soma Delights tenant runs on a Postgres cluster physically located in India.
- The somaerp backend serving that cluster runs in the same region.
- Customer personal data never crosses a border because the deployment never crosses one.

For a future EU tenant (hypothetical): the operator stands up a separate Postgres + somaerp pair in an EU region. The same Docker image, the same schema. The two deployments do not share data because there is no replication path between them.

This is a **deployment-topology guarantee**, not a code guarantee. The schema decisions in `00_multi_tenant_strategy.md` (UUID v7 PKs, no cross-tenant FKs) make per-region per-tenant deployments practical without code change.

## What changes at v1.0 (documented intent, not v0.9.0 scope)

The v1.0 multi-tenant sharding strategy (per `00_multi_tenant_strategy.md` Stage B) introduces a `meta.tenant_shards` lookup. Residency at v1.0 becomes:

- `meta.tenant_shards.region_code` declares which region a tenant lives in.
- `meta.tenant_shards.cluster_dsn` resolves to a cluster physically in that region.
- A tenant move across regions is an explicit ops procedure (snapshot, restore in target region, update lookup); it never happens silently.

Until v1.0 ships the sharding lookup, residency is what the operator deploys.

## Per-tenant data export — covered by tennetctl GDPR DSAR

tennetctl 03_iam already shipped a GDPR DSAR (Data Subject Access Request) primitive in v0.8.0 — see the iam `08_dsar` sub-feature. somaerp inherits this for free:

- A customer (or operator on their behalf) requests a DSAR via tennetctl.
- The DSAR primitive walks every tennetctl table for that subject.
- somaerp registers an export hook (planned; ships in 56-10 customers plan) that yields the somaerp `fct_customers` row plus joined subscription, delivery, and (where applicable) QC-attribution data for the subject.
- The export bundle is signed and made available via tennetctl vault.

DPDP Act § 12(d) "right to access" and § 12(b) "right to erasure" are both served through this primitive. somaerp adds the somaerp-side query plan; tennetctl owns the actor authentication, request audit, and bundle delivery.

## Per-tenant data deletion (right to erasure)

When a DSAR deletion request arrives:

- tennetctl marks the iam user as deleted.
- somaerp soft-deletes the `fct_customers` row (`deleted_at = NOW()`) and all child subscriptions, delivery routes (memberships), and customer-attached attribute rows.
- somaerp anonymizes — does NOT delete — historical `evt_inventory_movements`, `evt_qc_checks`, and `fct_production_batches`. These rows are append-only and FSSAI requires their retention for the lot-traceability chain. The customer's identity is severed from the chain (e.g. by replacing customer references on `evt_delivery_stops` with a tombstone token), but the production-side audit trail stays intact.
- The same DSAR completion event records what was anonymized vs deleted, so a future inspector can verify the mapping.

This split (delete identity, retain anonymized batch trail) is the only legally defensible answer when food-safety regulation and personal-data regulation collide. Both are honored.

## FSSAI compliance — what somaerp must give an inspector

Soma Delights operates under FSSAI Basic Registration at Stage 1 and a State License from Stage 3 onward (`compliance-food-safety.md`). FSSAI's two pillars somaerp must support:

### Pillar 1: lot-tracked traceability from raw material to bottle

Per ADR-006, every raw material receipt records `lot_number` on `dtl_procurement_lines`. Every consumption emits `evt_inventory_movements (movement_type='consumed', batch_id_ref=<batch>, lot_number=<lot>)`. A single graph walk answers "which batches consumed lot X":

```text
SELECT batch.*, evt.quantity, evt.created_at
  FROM fct_production_batches batch
  JOIN evt_inventory_movements evt
    ON evt.batch_id_ref = batch.id
 WHERE evt.tenant_id = ctx.workspace_id
   AND evt.lot_number = ?
   AND evt.movement_type = 'consumed'
```

The inverse ("which lots went into batch Y") is the same query in the other direction. The FSSAI inspector's hardest question — "you got bad spinach on Tuesday from supplier Z; which Tuesday batches went out the door using it?" — is one query.

### Pillar 2: documented per-batch quality control

Per ADR-005, every batch carries one or more `evt_qc_checks` rows with checkpoint, performed-by user, result, optional notes, and optional `photo_vault_key`. The chain is immutable: a wrong check produces a corrective check, not an edit.

For the inspector: `SELECT * FROM evt_qc_checks WHERE batch_id = ? ORDER BY created_at` is the per-batch QC paper trail. Photos resolve via `photo_vault_key` against tennetctl vault per `04_integration/03_vault_for_secrets_and_blobs.md`.

### Label compliance is a label-rendering concern

FSSAI label requirements (`compliance-food-safety.md`) — ingredient list, net quantity, MFG/EXP, FSSAI license number, batch number — are rendered from the batch + product + recipe data already in somaerp. The label printing UX (which is in the production sub-feature) is a downstream plan; the data it needs is already in `fct_production_batches`, `fct_recipes`, `dtl_recipe_ingredients`, and the tenant's FSSAI license number stored in tennetctl vault as `somaerp.tenants.{workspace_id}.fssai_license_number`.

## DPDP Act 2023 — what somaerp must give the regulator

Per `customer-data-privacy.md` and the iam memory rules:

| DPDP obligation | How somaerp+tennetctl satisfies it |
| --- | --- |
| Lawful purpose declared per data point | The data_model docs declare every column's purpose; the privacy policy template ships in `customer-data-privacy.md` |
| Consent capture | Captured at customer signup via tennetctl iam consent primitives; somaerp `fct_customers.properties.consent_received_at` mirrors the timestamp |
| Purpose limitation | somaerp never uses customer data for advertising; no third-party data export path exists in code |
| Data minimization | The `fct_customers` schema collects only fields the data_model doc justifies; allergy data is in `dtl_attrs` not on the fact row |
| Right to access | tennetctl DSAR + somaerp export hook |
| Right to correction | tennetctl iam profile edit + PATCH `/v1/somaerp/customers/{id}` |
| Right to erasure | DSAR deletion + somaerp soft-delete + FSSAI-compatible anonymization |
| Storage limitation | tenant config declares retention windows per category; a scheduled job (deferred to v0.10) closes inactive customer records after the window |
| Security safeguards | tennetctl iam handles auth, sessions, RBAC; vault encrypts secrets at rest |
| Breach notification | tennetctl audit + notify primitives provide the breach-response paper trail |

DPDP § 9 ("reasonable security safeguards") is satisfied by the combined posture: TLS in transit, vault for secrets at rest, iam-enforced RBAC, audit on every mutation, no payment card data ever stored (payment processor handles per PCI-DSS — out of v0.9.0 scope, billing deferred).

## Cross-border transfer rules

DPDP Act allows cross-border transfer to permitted jurisdictions notified by the central government. v0.9.0's stance:

- Soma Delights data does not leave India (single-region deployment).
- Backups stay in India (operator's deployment choice; documented in deployment runbook, not code).
- No third-party data processor outside India is used (no external SaaS — empire thesis enforces).
- A future tenant in a jurisdiction with stricter cross-border rules (EU GDPR Schrems II) gets a separate deployment in that region.

The "no external SaaS" empire-thesis posture is also a cross-border posture: by never depending on a hosted external service, somaerp never accidentally ships customer data to a US-hosted SaaS endpoint.

## Audit emission category for compliance-relevant events

Every FSSAI-relevant or DPDP-relevant action emits an audit event with the appropriate category (per `04_integration/02_audit_emission.md`):

- `category=compliance` for QC checks, batch completion, lot consumption, label print.
- `category=privacy` for consent capture, DSAR access, DSAR deletion.
- `category=critical` for FSSAI-defined breaches (out-of-temperature delivery, failed QC on a delivered batch, missing batch number).

Audit retention follows tennetctl audit defaults; for a Soma Delights inspector visit, the inspector queries `category IN ('compliance', 'critical')` for the date range they care about and gets a complete paper trail.

## What is NOT in v0.9.0 scope

- Automated FSSAI return filing (deferred — annual paper return today).
- Automated DPDP breach notification submission to the Data Protection Board (deferred until DPBI publishes a programmatic submission interface).
- Differential privacy or k-anonymity for analytics (out of scope; somaerp analytics are tenant-scoped only).
- Cross-tenant federated reporting (impossible by construction — no cross-tenant FKs).

## Related documents

- `00_multi_tenant_strategy.md` — sharding enables per-region deployment
- `01_multi_region_kitchen_topology.md` — region declaration on `dim_regions` and `fct_locations`
- `../00_main/08_decisions/005_qc_checkpoint_model.md`
- `../00_main/08_decisions/006_inventory_and_procurement_model.md`
- `../04_integration/02_audit_emission.md`
- `../04_integration/03_vault_for_secrets_and_blobs.md`
- `99_business_refs/somadelights/09-execution/customer-data-privacy.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
- Memory: `feedback_audit_scope_mandatory.md`
