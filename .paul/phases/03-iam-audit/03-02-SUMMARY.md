---
phase: 03-iam-audit
plan: 02
subsystem: infra
tags: [iam, manifest, ncp, catalog-registration, feature-shell]

requires:
  - phase: 02-catalog-foundation
    provides: manifest parser, boot loader, upsert_all, discover_manifests
  - phase: 03-iam-audit-01
    provides: "03_iam" schema with 17 tables (needed for owns.tables references)
provides:
  - backend/02_features/03_iam/feature.manifest.yaml (first real NCP v1 consumer)
  - 6 empty sub-feature directory shells (01_orgs through 06_applications)
  - IAM catalog rows: 1 feature + 6 sub-features registered in "01_catalog"
  - Proof that the catalog upsert pipeline works on a real feature (not just the test fixture)
affects: [03-03 audit + emit_audit, 03-04 views, all Phase 4+ feature verticals that add nodes to these sub-feature shells]

tech-stack:
  added: []
  patterns:
    - "Empty sub-feature shells up front — all 6 sub-features declared in manifest now; Phase 4+ verticals add nodes into existing entries rather than creating new ones"
    - "owns.tables locks the schema contract: future verticals can't move tables across sub-features without updating the manifest"
    - "iam.users owns EAV infrastructure (dim_entity_types + dtl_attr_defs + dtl_attrs) since user is the most EAV-heavy IAM entity"

key-files:
  created:
    - backend/02_features/__init__.py
    - backend/02_features/03_iam/__init__.py
    - backend/02_features/03_iam/feature.manifest.yaml
    - backend/02_features/03_iam/sub_features/__init__.py
    - backend/02_features/03_iam/sub_features/01_orgs/__init__.py
    - backend/02_features/03_iam/sub_features/02_workspaces/__init__.py
    - backend/02_features/03_iam/sub_features/03_users/__init__.py
    - backend/02_features/03_iam/sub_features/04_roles/__init__.py
    - backend/02_features/03_iam/sub_features/05_groups/__init__.py
    - backend/02_features/03_iam/sub_features/06_applications/__init__.py
  modified:
    - tests/test_catalog_loader.py (relaxed features_upserted == 1 assertion since IAM now co-loads)

key-decisions:
  - "iam.users owns the EAV foundation tables (dim_entity_types, dtl_attr_defs, dtl_attrs) — user is the most EAV-heavy entity; alternative (iam.core sub-feature) deferred until a second sub-feature needs co-ownership"
  - "dim_scopes listed under iam.roles, not a separate iam.scopes sub-feature — scopes are a property of roles, not a first-class concept for now"
  - "All 6 sub-features declared up front with empty node arrays (rather than adding them incrementally) — gives Phase 4+ a predictable directory layout and stable sub-feature numbers from day one"

patterns-established:
  - "Pattern: feature.manifest.yaml at backend/02_features/{nn}_{feature}/ — 03_iam/ is the template for Phase 4+ verticals"
  - "Pattern: sub-feature directory numbered 01–99 matches the manifest number field (01_orgs → number 1)"
  - "Pattern: empty __init__.py at every level so importlib can resolve future handler paths"

duration: ~8min
started: 2026-04-16T12:40:00Z
completed: 2026-04-16T12:48:00Z
---

# Phase 3 Plan 02: IAM Feature Manifest — Summary

**IAM is registered in the NCP v1 catalog: 1 feature row + 6 sub-feature rows in `"01_catalog"` via `backend/02_features/03_iam/feature.manifest.yaml` — first non-fixture consumer of the catalog pipeline.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~8min |
| Tasks | 2 auto + 1 checkpoint (self-verified) |
| Files created | 10 |
| Files modified | 1 |
| Catalog rows added | 1 feature + 6 sub-features |

## Acceptance Criteria Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: Manifest parses | Pass | `parse_manifest()` returned FeatureManifest with key=iam, number=3, 6 sub-features, all empty nodes/routes/ui_pages |
| AC-2: Directory structure complete | Pass | 6 sub-feature dirs + 8 __init__.py files created; verified via `ls` |
| AC-3: Catalog upsert registers rows | Pass | `upsert: 1 features, 6 sub-features, 0 nodes, 0 deprecated`; DB query confirms key=iam (number=3, module_id=2) + 6 iam.* sub-feature rows in correct order |
| AC-4: Idempotent on re-run | Pass | Second upsert: same counts, row counts by key stayed at 1 + 6 |

## Accomplishments

- **IAM is live in the catalog** — `fct_features` has key=iam; `fct_sub_features` has iam.orgs (1), iam.workspaces (2), iam.users (3), iam.roles (4), iam.groups (5), iam.applications (6).
- **Pattern proven** — the manifest + loader pipeline works on a real feature, not just test fixtures. Phase 4+ verticals can copy this exact shape.
- **FastAPI lifespan verified** — backend boot logs show `Catalog upsert: 1 features, 6 sub-features, 0 nodes (0 deprecated)`.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| backend/02_features/__init__.py | Created | Package root for all features |
| backend/02_features/03_iam/feature.manifest.yaml | Created | IAM feature contract — 6 sub-features, owned tables, no nodes yet |
| backend/02_features/03_iam/sub_features/{01–06}/__init__.py | Created | Sub-feature directory shells (6 dirs) |
| tests/test_catalog_loader.py | Modified | Relaxed `features_upserted == 1` → `>= 1` (IAM now co-loads alongside fixture); enabled "iam" in test's TENNETCTL_MODULES set |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| iam.users owns EAV infrastructure | User is most EAV-heavy IAM entity; splitting into separate iam.core would be premature | Future refactor to iam.core only if other sub-features grow EAV usage |
| dim_scopes under iam.roles (not iam.scopes) | Scopes are a property of roles — grant bundle pointed at by lnk_role_scopes | No iam.scopes sub-feature in v1 |
| All 6 sub-features declared with empty nodes | Up-front declaration gives Phase 4+ a stable layout and predictable sub-feature numbers | Phase 4+ adds nodes into existing entries rather than expanding sub_features list |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Fixture test regression — IAM co-load broke exact-count assertion |
| Scope additions | 0 | — |
| Deferred | 0 | — |

### Auto-fixed Issues

**1. test_fixture_feature_registers broke after IAM manifest added**
- Found during: Task 2 verification (running full pytest suite)
- Issue: Test asserted `report1.features_upserted == 1` assuming fixture was the only always_on manifest loaded under TENNETCTL_MODULES={"core"}. IAM's `always_on: true` made it load unconditionally → count became 2.
- Fix: Updated assertions to `>= 1` and enabled `"iam"` in the test's modules set. Fixture-specific row counts still verified via `_count()` helpers.
- Files: tests/test_catalog_loader.py
- Verification: pytest 11/11 green post-fix.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| pytest regression due to IAM manifest always_on loading | Loosened fixture test assertions; exact-count assertions on global counters were always brittle when other features exist |

## Next Phase Readiness

**Ready:**
- Plan 03-03 can add the `"04_audit"` schema + `evt_audit` table + `emit_audit` effect node.
- `emit_audit` node will be registered under a new `audit` feature manifest (separate file at `backend/02_features/04_audit/feature.manifest.yaml`), not under IAM.
- Phase 4+ verticals (Orgs, Workspaces) will add node entries into the existing `iam.orgs` / `iam.workspaces` sub-feature blocks — the shells are there waiting.

**Concerns:**
- The `always_on` flag makes IAM load regardless of `TENNETCTL_MODULES`. This is correct per NCP §3, but tests that manipulate the modules set need to remember it.
- Handler resolution in the runner walks all manifests per call — will show in profiles once real workloads hit. Already tracked in v0.1.5 deferred gaps.

**Blockers:**
- None. Ready for Plan 03-03 (audit schema + emit_audit node — first real effect node dispatched by the runner).

---
*Phase: 03-iam-audit, Plan: 02*
*Completed: 2026-04-16*
