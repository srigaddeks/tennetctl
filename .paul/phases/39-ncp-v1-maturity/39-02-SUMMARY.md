---
phase: 39-ncp-v1-maturity
plan: 39-02
subsystem: repository-pattern
tags: [ncp-v1, get_many, n+1, bulk-reads, docs]

requires:
  - phase: 39-ncp-v1-maturity
    plan: "39-01"
    provides: coherent NCP spec foundation
provides:
  - `get_many` pattern shipped on 3 canonical IAM repos
  - Pattern authoritative in backend standards (02_contributing_guidelines/05)
affects: [every future repo; opportunistic rollout to remaining ~27 repos]

tech-stack:
  added: []
  patterns:
    - "Bulk read: WHERE id = ANY($1::varchar[]) returning dict keyed by id"

key-files:
  modified:
    - backend/02_features/03_iam/sub_features/01_orgs/repository.py
    - backend/02_features/03_iam/sub_features/02_workspaces/repository.py
    - backend/02_features/03_iam/sub_features/03_users/repository.py
    - 02_contributing_guidelines/05_backend_api_standards.md

key-decisions:
  - "get_many returns dict[str, dict] (not list) — enables O(1) caller lookup; missing ids simply absent"
  - "Empty ids → empty dict (no query) — avoids 0-arg ANY() edge case"
  - "Column list mirrors get_by_id exactly — substitutability"

duration: ~10min
---

# Phase 39 Plan 02: get_many Bulk Pattern Summary

**N+1 killer shipped on orgs/workspaces/users; pattern codified in backend standards.**

## AC Results

| Criterion | Status |
|---|---|
| AC-1: get_many on 3 IAM repos | PASS |
| AC-2: Convention documented | PASS |

## Files Changed

| File | Change |
|---|---|
| orgs/repository.py | +get_many (~14 LoC) |
| workspaces/repository.py | +get_many (~14 LoC) |
| users/repository.py | +get_many (~14 LoC) |
| 02_contributing_guidelines/05_backend_api_standards.md | +"Bulk reads: get_many" subsection under repository rules (~30 LoC) |

## Verification

- ✓ All 3 repos import clean; `hasattr(repo, 'get_many')` True on each
- ✓ Pyright clean on all 3 sub-features
- ✓ Standards doc has the full subsection with signature + SQL template + contract

## Next

- 39-03 (v1→v2 versioning demo on one real node) — last plan in phase 39
- Opportunistic rollout on remaining ~27 repos whenever touched

---
*Completed 2026-04-20*
