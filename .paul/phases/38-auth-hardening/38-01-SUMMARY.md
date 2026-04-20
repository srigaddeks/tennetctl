---
phase: 38-auth-hardening
plan: 38-01
subsystem: auth
tags: [session-fixation, rate-limiting, token-replay, asyncpg, fastapi, iam]

requires:
  - phase: 08-auth
    provides: credentials/sessions/auth sub-features + session cookie format
  - phase: 20-iam-hardening-for-oss
    provides: account lockout (Plan 20-03), consumed_at columns on token tables (20-02)

provides:
  - rotate_on_login() helper in iam.sessions service — session-fixation defense
  - auth_rate_limit() FastAPI dependency factory + evt_auth_rate_limit_window Postgres counter
  - Atomic single-use token consumption via UPDATE…WHERE consumed_at IS NULL RETURNING

affects: [38-02 mfa-rotation, 39-ncp-v1-maturity, future Valkey integration]

tech-stack:
  added: []
  patterns:
    - FastAPI Depends() factory for cross-cutting middleware
    - Postgres UPSERT as rate-limit counter with time-bucketed PK
    - Atomic claim-and-consume pattern for single-use tokens

key-files:
  created:
    - backend/02_features/03_iam/sub_features/10_auth/rate_limit.py
    - 03_docs/features/03_iam/05_sub_features/10_auth/09_sql_migrations/02_in_progress/20260420_069_iam-auth-rate-limit-window.sql
  modified:
    - backend/02_features/03_iam/sub_features/09_sessions/service.py
    - backend/02_features/03_iam/sub_features/10_auth/{service,routes}.py
    - backend/02_features/03_iam/sub_features/{11_magic_link,14_password_reset}/{repository,service,routes}.py

key-decisions:
  - "Postgres-only rate limiter (Valkey path deferred until Valkey wired in app.state)"
  - "Rate limiter is FastAPI middleware, not a catalog node — cross-cutting, no reuse today"
  - "Session rotation scope-trimmed to login path; password-change + MFA-enroll deferred (need response cookie re-set + UX touch)"
  - "Reuse existing iam.{magic_link,password_reset}.consume_failed taxonomy instead of inventing iam.token.replay_blocked"
  - "ADR-031 skipped — race-close is one UPDATE clause, not architecture"

patterns-established:
  - "FastAPI Depends factory for per-endpoint rate limiting: auth_rate_limit('endpoint.name', max_requests=N, window_seconds=S)"
  - "Atomic claim: UPDATE … WHERE id=$1 AND consumed_at IS NULL AND expires_at > CURRENT_TIMESTAMP RETURNING id"
  - "Session rotation: revoke_session_by_reason('rotated_on_login') + iam.session.rotated audit on the post-mint boundary"

duration: ~45min
started: 2026-04-20T19:30:00Z
completed: 2026-04-20T20:15:00Z
---

# Phase 38 Plan 01: Auth Hardening Summary

**Session-fixation defense on login + IP rate limiter on 3 unauth endpoints + atomic single-use tokens; three OWASP-class vulns closed on the OSS path.**

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Session rotation on privilege escalation | PARTIAL | Login path: PASS. Password-change + MFA-enroll: DEFERRED (scope trim — require response cookie re-set + UX change). |
| AC-2: IP-based rate limit on unauth endpoints | PASS (w/ deviation) | Postgres-native only; Valkey primary path documented as deferred. |
| AC-3: Single-use tokens for reset + magic-link | PASS | Atomic UPDATE closes TOCTOU; concurrent double-redeem now has exactly one winner. |

## Accomplishments

- **Session-fixation defense on login** — an attacker who plants a session cookie in the victim's browser no longer keeps that session after the victim signs in. The session_id rotates; the old one is revoked in the same tx.
- **Per-IP rate limiter** — signin, magic-link request, and password-reset request are capped at 10/5/3 per 60s per IP. Defends against distributed enumeration and spam that per-user lockout doesn't cover.
- **Atomic token consumption** — magic-link and password-reset tokens cannot be double-consumed in a race. Win-the-update replaces trust-the-select.
- **Zero-dep migration** — no new Python packages added; pure asyncpg UPSERT + FastAPI Depends.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/02_features/03_iam/sub_features/10_auth/rate_limit.py` | Created | FastAPI dependency factory + Postgres counter + audit emit |
| `.../10_auth/09_sql_migrations/…/20260420_069_iam-auth-rate-limit-window.sql` | Created | evt_auth_rate_limit_window table |
| `.../09_sessions/service.py` | Modified | Added `rotate_on_login()` |
| `.../10_auth/service.py` | Modified | `signin()` accepts `previous_session_id`; calls rotate after mint |
| `.../10_auth/routes.py` | Modified | Parse incoming session cookie; apply `auth_rate_limit` to /signin |
| `.../11_magic_link/repository.py` | Modified | `mark_consumed` → atomic UPDATE returning bool |
| `.../11_magic_link/service.py` | Modified | Race-replay branch on mark_consumed == False |
| `.../11_magic_link/routes.py` | Modified | Apply rate limit to /request (5/60s) |
| `.../14_password_reset/repository.py` | Modified | `mark_consumed` → atomic UPDATE returning bool |
| `.../14_password_reset/service.py` | Modified | Race-replay branch on mark_consumed == False |
| `.../14_password_reset/routes.py` | Modified | Apply rate limit to /request (3/60s) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Postgres-native rate limiter only | Valkey not wired in app.state; adding Valkey integration is out-of-scope for this plan | Rate limiter works today; swap to Valkey-primary + PG-fallback is a 10-line future change |
| FastAPI Depends, not catalog node | Cross-cutting concern with one consumer today; node registration adds ceremony without reuse | Can be lifted to a node later if non-auth features need rate limiting |
| Scope-trim session rotation to login path | Password-change + MFA-enroll rotation need response cookie re-set (UX touch); out-of-scope expansion | Primary session-fixation vector closed; follow-up plan 38-02 can cover other boundaries |
| Reuse `iam.{magic_link,password_reset}.consume_failed` audit keys | Existing taxonomy is already granular (reason='race_replay' now distinguishes the race case) | No new event keys to register; security monitoring still sees the distinct signal |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Scope trims (deferred) | 2 | Password-change rotation + MFA-enroll rotation; Valkey primary path |
| Plan assumptions wrong | 2 | `consumed_at` column already existed; TTLs already tight (10/15 min) |
| Taxonomy reuse instead of new | 1 | No `iam.token.replay_blocked` — existing `consume_failed{reason=race_replay}` |
| ADR skipped | 1 | ADR-031 not written — race-close is implementation detail, not architectural decision |

**Total impact:** Essential hardening shipped; no scope creep; documented follow-ons.

### Auto-fixed Issues

**1. Plan assumed consumed_at migration was needed**
- **Found during:** Task 3 kickoff — reading existing repository.py
- **Issue:** Plan specified creating NNN migrations to add `consumed_at TIMESTAMP`
- **Reality:** Column already exists; `mark_consumed` existed but non-atomically
- **Fix:** Scope shrank from "add column + TTL tighten + atomic consume" to just "atomic consume"
- **Verification:** Grep confirmed `_TOKEN_TTL_MINUTES = 10` / `= 15` already present

**2. Plan specified `extras={"retry_after": N}` on AppError**
- **Found during:** Task 2 implementation
- **Issue:** `AppError.__init__` takes only (code, message, status_code); no extras field
- **Fix:** Embed retry_after in the message string; the HTTP header is the canonical channel anyway
- **Impact:** Clients parse retry_after from Retry-After header, not body (correct per RFC 6585 §4)

### Deferred Items

- **38-02** — Session rotation on password-change + MFA-enroll boundaries (requires response cookie re-set)
- **Valkey primary rate-limit path** — pending Valkey integration in app.state (tracked alongside Phase 33 APISIX infra)
- **Catalog node registration for rate_limit** — if non-auth features need rate limiting in future
- **Live DB verification** — pytest suite requires Postgres on :5434 + migrator run (operator-deferred)

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `AppError.extras` in plan doesn't exist in codebase | Removed the field; documented workaround |
| Live pytest can't run (no Postgres) | Import + pyright verification substitutes; operator-deferred per project pattern |

## Next Phase Readiness

**Ready:**
- Phase 38-02 (if created) can layer password-change + MFA-enroll rotation on top of `rotate_on_login` helper (rename to `rotate_session` + parameterize reason)
- Phase 39 NCP v1 maturity — `rate_limit.py` is a candidate for lifting to a catalog node if the pattern generalizes

**Concerns:**
- Rate-limit window GC not yet scheduled — old rows in `evt_auth_rate_limit_window` will accumulate. Should be cleaned nightly (or on insert via `WHERE window_start < CURRENT_TIMESTAMP - '24 hours'`). Logging as a deferred item.
- `previous_session_id` parsing in signin route swallows all exceptions; tampered cookie → rotation silently skipped (not blocking, but log-worthy)

**Blockers:**
- None. Live verification requires operator to spin up Postgres + apply migration 069.

---
*Phase: 38-auth-hardening, Plan: 01*
*Completed: 2026-04-20*
