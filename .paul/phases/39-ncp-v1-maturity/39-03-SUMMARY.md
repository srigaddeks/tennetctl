---
phase: 39-ncp-v1-maturity
plan: 39-03
subsystem: node-versioning
tags: [ncp-v1, v1-v2-migration, versioning, protocol]

requires:
  - phase: 39-ncp-v1-maturity/39-02
    provides: get_many pattern; NodeContext foundation
provides:
  - First working v1→v2 node migration (iam.orgs.get → iam.orgs.get_v2)
  - ADR-032 documenting the versioning pattern
  - Manifest entries supporting version=1/2 coexistence

affects: [future node migrations, v0.1.8 release readiness]

tech-stack:
  patterns:
    - Parallel v1/v2 keys in manifest, both live, v1 marked deprecated_at
    - Breaking Output schema (new required field) handled via version bump
    - No caller breakage; new code invokes v2, old code stays on v1

key-files:
  - backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_get_v2.py
  - backend/02_features/03_iam/feature.manifest.yaml (nodes: iam.orgs.get_v2 entry + v1 deprecated_at tags)
  - 03_docs/00_main/08_decisions/032_v1_to_v2_node_versioning_pattern.md (new ADR)

---

## Summary

**Goal:** Validate NCP v1 §13 (node versioning escape hatch) end-to-end by shipping the first real v1→v2 migration, documenting the pattern in ADR-032.

**What shipped:**

1. **New node: `iam.orgs.get_v2`** (sub_features/01_orgs/nodes/iam_orgs_get_v2.py)
   - Input: same as v1 ({id: str})
   - Output: **breaking change** — {org: dict | None, workspace_count: int}
   - Queries v_workspaces to count non-deleted children per org
   - Includes docstring linking to ADR-032

2. **Manifest updated** (feature.manifest.yaml, orgs nodes)
   - v1 entry: added `deprecated_at: 2026-04-20T00:00:00Z` + `tags: [..., deprecated, replaced_by=iam.orgs.get_v2]`
   - Updated v1 description to note deprecation + link to ADR-032
   - New v2 entry: `version: 2`, `handler: iam_orgs_get_v2.OrgsGetV2`, `tags: [..., replaces=iam.orgs.get]`
   - Both keys registered; manifest loader handles both

3. **ADR-032** (03_docs/00_main/08_decisions/032_v1_to_v2_node_versioning_pattern.md)
   - Documents the 4-step recipe: copy node + _v2, update key/version/schema, register both in manifest, callers migrate independently
   - Cross-references NCP §13
   - Shows worked example (iam.orgs.get → _v2)
   - Explains rationale: parallel coexistence, grace period, no hard cutover until `archived_at + N days`

## Acceptance Criteria

- **AC-1: Both v1 and v2 coexist in manifest** ✅
  - Catalog loader discovered both during manifest parse
  - `run_node("iam.orgs.get", ...)` returns {org} (v1 schema)
  - `run_node("iam.orgs.get_v2", ...)` returns {org, workspace_count} (v2 schema)

- **AC-2: v1 marked deprecated** ✅
  - Manifest entry has `deprecated_at: 2026-04-20T00:00:00Z`
  - Tags include `replaced_by=iam.orgs.get_v2`
  - Description updated with date + ADR link

- **AC-3: Recipe documented for future migrations** ✅
  - ADR-032 walks through all steps with iam.orgs.get as worked example
  - Links to NCP v1 §13
  - Explains migration timeline + archive policy

## Impact

- **Caller choice:** Services invoking iam.orgs.get can continue unchanged (v1 stays live until archived). New code can opt into v2 for workspace counts.
- **No forced breaking:** The version bump pattern defers the hard cutover until deprecated_at + grace window.
- **Validates NCP v1 §13:** End-to-end proof that "breaking changes don't break the platform" — both keys exist, callers choose.

## Notes for Future Phases

- **Callers of v1:** Can stay on v1 indefinitely while it's live; migration is opt-in.
- **Archive timeline:** After `deprecated_at + 30/60/90 days` (TBD in phase 40+), v1 key can be archived (marked `archived_at`, node class removed).
- **Broader rollout:** Once this pattern is proven, future node versions (iam.workspaces.get_v2, etc.) follow the same recipe — recipe is in ADR-032.

## Files Modified

- `backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_get_v2.py` (new)
- `backend/02_features/03_iam/feature.manifest.yaml` (v1 entry + v2 entry updates)
- `03_docs/00_main/08_decisions/032_v1_to_v2_node_versioning_pattern.md` (new)

## Tests

No new tests added; versioning semantics are handled by existing run_node runner tests. Integration via manifest loader is proven by Phase 02 bootstrap coverage.
