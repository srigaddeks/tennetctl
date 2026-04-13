# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-13)

**Core value:** Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in.
**Current focus:** v0.1 Foundation + IAM — Phase 2 Schema & Audit Foundation

## Current Position

Milestone: v0.1 Foundation + IAM
Phase: 2 of 6 (Schema & Audit Foundation)
Plan: Not started
Status: Ready to plan Phase 2
Last activity: 2026-04-13 — Phase 1 complete (Core Infrastructure), transitioned to Phase 2

Progress:
- Milestone: [██░░░░░░░░] 17%
- Phase 1: [██████████] 100% ✅ Complete
- Phase 2: [░░░░░░░░░░] 0% (not started)

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ○        ○        ○     [Ready to plan Phase 2]
```

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: ~20 min
- Total execution time: ~1 hour

**By Phase:**

| Phase | Plans | Total Time | Avg/Plan |
|-------|-------|------------|----------|
| 01-core-infrastructure | 3/3 ✅ | ~60min | ~20min |

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| Raw SQL with asyncpg, PG-specific features allowed | Init | No ORM |
| Audit in 04_audit schema, cross-cutting | Planning | All features write evt_audit |
| Every phase is a vertical slice | Planning | Schema → repo → service → routes → nodes → UI → Playwright |
| Custom SQL migrator over Alembic/ORM | Phase 1 | asyncpg-only, UP/DOWN, rollback, history |
| Postgres on port 5434 | Phase 1 | Local PG on 5432 |
| Migrator in backend/ not scripts/ | Phase 1 | backend/01_migrator/ + backend/00_setup/migrations/ |
| Frozen dataclass Config, not BaseSettings | Phase 1 | Simpler, no extra dep |
| importlib everywhere for numeric dirs | Phase 1 | Project convention |
| Frontend port 51735 (non-standard) | Phase 1 | All E2E tests + CORS use 51735 |
| E2E: Suite Setup/Teardown + data-testid | Phase 1 | Browser lifecycle at suite level, resilient selectors |
| ApiClientError class (code + statusCode) | Phase 1 | Typed error discrimination in UI |

### Git State
Last commit: 66ed003
Branch: feat/pivot

### Deferred Issues
None.

### Blockers/Concerns
None.

## Session Continuity

Last session: 2026-04-13
Stopped at: Phase 1 complete, Phase 2 not yet started
Next action: /paul:plan for Phase 2 (Schema & Audit Foundation)
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
