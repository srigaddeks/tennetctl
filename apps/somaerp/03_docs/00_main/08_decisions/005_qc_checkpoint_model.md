# ADR-005: QC checkpoint model — multi-stage definition + immutable check event log
Status: ACCEPTED
Date: 2026-04-24

## Context

FSSAI compliance for a cold-pressed juice operation requires documented quality control at multiple stages: pre-production checks on raw materials (visual freshness, smell), in-production checks (temperature, pressing yield, taste), post-production checks (bottle weight, label correctness, refrigeration temperature), and FSSAI-mandated traceability checks (lot-to-batch linkage, expiry dating). Each check produces a result that must be permanently recorded with the actor, timestamp, and (for visual checks) photo evidence. The decision is how to model the checkpoint definitions (which checks exist for which recipe steps) separately from the check execution events (one row per actual check performed on an actual batch).

## Decision

**QC is modeled in two layers. (1) Definitions: `dim_qc_stages` (pre_production, in_production, post_production, fssai), `dim_qc_check_types` (visual, smell, weight, temperature, taste, lot_traceability), and `dim_qc_checkpoints` (per recipe-step or per batch-stage, with `criteria_jsonb` carrying threshold/expected-value/pass-conditions). (2) Execution: `evt_qc_checks (id, tenant_id, batch_id, checkpoint_id, performed_by_user_id, result, notes, photo_vault_key, created_at)` — append-only, immutable, no `updated_at`, no `deleted_at`.** Photos are stored in the tennetctl vault primitive (or its blob extension) and referenced by `photo_vault_key` on the event row. A failed QC check on a batch transitions the batch to a `qc_failed` substate but does NOT mutate the event row — corrections are new event rows, never edits.

## Consequences

- **Easier:** FSSAI audit produces an immutable, append-only paper trail per batch with photo evidence and actor attribution.
- **Easier:** QC checkpoint definitions can evolve over time (new check types, revised criteria) without rewriting historical check events; old events still reference the checkpoint version they were taken against.
- **Easier:** querying "every QC failure in the last 30 days at KPHB Kitchen" is a single indexed scan over `evt_qc_checks`.
- **Harder:** correcting a wrongly-recorded check requires inserting a corrective event with a `correction_of` pointer rather than editing the original. The service layer encapsulates this.
- **Harder:** photo upload depends on the tennetctl vault blob extension (or a vault-backed signed-URL pattern). Until the vault has a blob primitive, photos may need to be stored as base64 in vault secrets — flagged in `04_integration/03_vault_for_secrets_and_blobs.md`.
- **Constrains:** the quality data model layer (`01_data_model/04_quality.md`); the production batch lifecycle (ADR-007 — batch state can be `qc_failed`); the audit emission keys (`somaerp.quality.checks.recorded`).

## Alternatives Considered

- **Mutable check rows (one per batch-checkpoint, updated as checks happen).** Simplest. Rejected: destroys the FSSAI paper trail and breaks the project-wide append-only-`evt_*` rule.
- **All checks as a single JSONB blob on the batch row.** Avoids new tables. Rejected: kills queryability across batches, breaks photo attachment semantics, and cannot be partially indexed.
- **No checkpoint definitions, just free-form check events.** Simplest write path. Rejected: every check event becomes a string-typed mystery; criteria evolution is impossible to track; recipe-step-to-checkpoint mapping is lost.
- **Photos in a separate object-storage bucket, not vault.** Avoids the vault-blob dependency. Rejected: violates the empire thesis (no external SaaS); vault is the project's single secret/blob primitive.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/05-operations/operations-model.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
- `apps/somaerp/03_docs/04_integration/03_vault_for_secrets_and_blobs.md`
- `apps/somaerp/03_docs/00_main/08_decisions/007_production_batch_lifecycle.md`
