---
phase: 56-somaerp-foundation
plan: 06
subsystem: kitchen_capacity
tags: [somaerp, capacity, time-window, validity-history]
duration: ~15 min (autonomous; session interrupted mid-plan then resumed with single full-stack subagent)
completed: 2026-04-24
---

# Phase 56 Plan 06: Kitchen Capacity Summary

**ADR-003 capacity model live: `fct_kitchen_capacity` (kitchen × product_line × time_window × valid_from/to) + `v_kitchen_current_capacity` + `v_kitchen_capacity_history`. KPHB Home Kitchen × Cold-Pressed Drinks × 50 bottles × 04:00-08:00 × valid_from 2026-04-24 row seeded live via API.**

## ACs

| AC | Status |
|---|---|
| AC-1: Migration + view + partial unique + CHECK constraints | PASS |
| AC-2: 5 endpoints under /kitchens/{id}/capacity with envelope + audit | PASS |
| AC-3: /geography/kitchens/[id] detail + /capacity/new form, tsc+build clean | PASS |
| AC-4: MCP walk | DEFERRED to final sweep |

## Files (12)

- Migration: `20260424_005_create-kitchen-capacity.sql`
- Backend sub-feature: `16_kitchen_capacity/` (5 files)
- main.py + manifest updates
- Frontend: `/geography/kitchens/[id]/page.tsx` + `/capacity/new/page.tsx`
- types + lib appends

## Deviations
- PATCH adds pre-check 409 CAPACITY_ALREADY_CLOSED + 422 INVALID_VALID_TO for friendlier errors (spec allowed just the DB-level check)
- Migration constraint prefix `chk_kc_*` vs longer `chk_somaerp_fct_kitchen_capacity_*` — consistency over length
- Session interruption mid-APPLY required resume with single full-stack subagent (both original parallel subagents had been killed)

Next: 56-07 recipes (includes user's "play with values" + BOM cost rollup + Equipment sub-feature).
