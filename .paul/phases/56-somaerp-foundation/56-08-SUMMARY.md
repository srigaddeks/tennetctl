---
phase: 56-somaerp-foundation
plan: 08
subsystem: quality_control
completed: 2026-04-24
---

# Plan 56-08: Quality Control — UNIFIED

**5 tables + 2 views. Polymorphic checkpoint scope (universal / recipe_step / raw_material / kitchen / product). Immutable evt_qc_checks event log. 3 universal dim seeds; zero tenant checkpoint/check seeds.**

## Schema
- dim_qc_check_types (8 seeded: visual/smell/firmness/weight/temperature/taste/lot_verification/document_check)
- dim_qc_stages (5 seeded: pre_production/in_production/post_production/fssai/receiving)
- dim_qc_outcomes (4 seeded: pass/fail/partial_pass/skipped)
- dim_qc_checkpoints — TENANT-SPECIFIC catalog with UUID PK (dim_* naming deviation, documented via COMMENT); polymorphic scope_kind + scope_ref_id with CHECK constraint
- evt_qc_checks — append-only, references checkpoint + batch_id (VARCHAR(36), TODO(56-10) FK — 56-10 now exists, can be promoted in cleanup)

## Endpoints
7+ under /v1/somaerp/quality/*: check-types, stages, outcomes (read); checkpoints CRUD; checks append-only + list.

## Frontend
/quality landing + /checkpoints list+new + /checks feed.

## Seed
**ZERO tenant checkpoints/checks** per user directive.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
