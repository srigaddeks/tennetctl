---
phase: 39-ncp-v1-maturity
plan: 39-01
subsystem: catalog
tags: [ncp-v1, NodeContext, docs]

requires:
  - phase: 02-catalog-foundation
    provides: NodeContext, runner, NCP v1 spec
provides:
  - `pool` as first-class NodeContext field (backward-compatible)
  - NCP v1 spec sync with runner reality (§6, §8, §9, §17 changelog)
affects: [39-02 get_many pattern, 39-03 v1→v2 versioning demo, every future sub-feature]

tech-stack:
  added: []
  patterns:
    - Additive field introduction with parallel backward-compat channel (extras["pool"] kept)

key-files:
  modified:
    - backend/01_catalog/context.py
    - 57 route/service/worker files — 63 NodeContext-builder patches
    - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md

key-decisions:
  - "Additive-only migration: pool= + extras[\"pool\"] both populated. Downstream ctx.extras[\"pool\"] readers untouched."
  - "Setup category gets the authz bypass explicitly (spec matched reality)"
  - "Control kind widened in spec to allow read-only DB ops"

duration: ~15min
started: 2026-04-20T21:00:00Z
completed: 2026-04-20T21:15:00Z
---

# Phase 39 Plan 01: NCP v1 Pool + Doc Sync Summary

**`pool` is now a first-class NodeContext field; spec drift closed on §6, §8, §9.**

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: `pool` first-class field | PASS | `ctx.pool` works; `ctx.extras["pool"]` unchanged; child_span propagates both |
| AC-2: All route builders populate the new field | PASS | 63 patches across 57 files; grep confirms no remaining `extras={"pool":` without sibling `pool=pool` |
| AC-3: Spec sync | PASS | §6 documents pool + extras; §8 documents kind semantics + control-read widening; §9 documents setup + failure bypasses; §17 changelog added |

## What Shipped

- `backend/01_catalog/context.py` — new `pool: Any = None` field between `conn` and `request_id`
- 57 files updated — Python batch script added `pool=pool,` as sibling kwarg to every `extras={"pool": pool}` site. Verified no drift.
- NCP v1 spec — §6 NodeContext rewritten with `pool` + `extras`; §8 new "Kind semantics" block with control-read widening; §9 "Audit-scope bypasses" subsection; §17 changelog

## Verification

| Check | Result |
|---|---|
| `pyright backend/01_catalog` | 0 errors |
| Smoke test: `NodeContext(pool='x').pool == 'x'` | PASS |
| Smoke test: `child_span` propagates pool | PASS |
| grep: every `extras={"pool":` has sibling `pool=pool` | PASS (0 gaps) |
| Pre-existing pyright errors in webpush/capabilities | Unchanged — unrelated to this plan |

## Deviations from Plan

None. Plan executed as written.

## Next Phase Readiness

- **39-02** (get_many pattern) — can proceed. Unblocked by nothing in particular; just the natural next maturity item.
- **39-03** (v1→v2 versioning demo) — can proceed. The spec foundation is now coherent.
- **Opportunistic cleanup** — downstream `ctx.extras["pool"]` readers (~21 call sites) can migrate to `ctx.pool` whenever they're next touched. No forcing function.

---
*Phase: 39-ncp-v1-maturity, Plan: 01*
*Completed: 2026-04-20*
