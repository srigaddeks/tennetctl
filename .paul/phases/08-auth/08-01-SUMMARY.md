---
phase: 08-auth
plan: 01
subsystem: auth
tags: [auth, sessions, credentials, oauth, argon2id, hmac, fastapi, asyncpg]

requires:
  - phase: 03-iam-audit
    provides: "03_iam schema — fct_sessions, dtl_credentials tables already migrated"
  - phase: 07-vault
    provides: "VaultClient for session signing key + argon2 pepper; bootstrap secrets seeded"

provides:
  - "IAM auth sub-features wired and test-verified: credentials (08), sessions (09), auth (10)"
  - "26 pytest tests passing: signup/signin/signout/me/session-expiry/oauth/credentials/sessions"
  - "Session middleware — optional auth injecting scope into request.state from vault-signed tokens"
  - "4 catalog nodes: iam.auth.signup, iam.auth.signin, iam.auth.validate_session, iam.auth.revoke_session"

affects: [08-02-frontend, 09-featureflags]

tech-stack:
  added: []
  patterns:
    - "Session middleware is open (never rejects) — routes guard themselves via request.state.user_id"
    - "OAuth tests fully monkeypatched — all 6 pass without real provider credentials"
    - "Session token is HMAC-SHA256 signed with vault key auth.session.signing_key_v1"
    - "Argon2id password hashing with vault pepper; password change revokes sibling sessions"

key-files:
  verified:
    - backend/01_core/middleware.py
    - backend/02_features/03_iam/feature.manifest.yaml
    - backend/02_features/03_iam/routes.py
    - backend/02_features/03_iam/sub_features/08_credentials/
    - backend/02_features/03_iam/sub_features/09_sessions/
    - backend/02_features/03_iam/sub_features/10_auth/
  tests:
    - tests/test_iam_auth_api.py
    - tests/test_iam_credentials_sessions_api.py
    - tests/test_iam_auth_oauth.py

key-decisions:
  - "OAuth tests monkeypatched: _exchange_google/_exchange_github stubs bypass real HTTP — all 6 pass anywhere"
  - "Session middleware requires vault on app.state — silently skips token validation if vault absent"

patterns-established:
  - "Auth sub-feature composes iam.users + iam.credentials + iam.sessions via importlib (no cross-import)"

duration: ~15min
started: 2026-04-16T00:00:00Z
completed: 2026-04-16T00:15:00Z
---

# Phase 8 Plan 01: Auth Backend — Wire + Test Summary

**IAM auth backend (credentials, sessions, auth flow) verified complete: 26 pytest tests passing, full suite 178/178 green.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Tasks | 3 completed |
| Test files | 3 |
| Tests passing | 26/26 |
| Full suite | 178/178 |
| Fixes needed | 0 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Auth routes mounted + nodes in catalog | Pass | Server starts clean; 4 iam.auth.* nodes visible in /v1/catalog/nodes |
| AC-2: test_iam_auth_api.py passes | Pass | 8/8 — signup, signin, signout, /me, session expiry, validate_session node, audit |
| AC-3: test_iam_credentials_sessions_api.py passes | Pass | 12/12 — password change, session list/get/extend/delete, scoping |
| AC-4: OAuth tests no ERROR | Pass | 6/6 — fully monkeypatched; no real OAuth credentials needed |

## Accomplishments

- All three auth sub-features were already correctly implemented and needed zero fixes
- Session middleware properly validates vault-signed HMAC-SHA256 tokens; open by default (never rejects)
- OAuth flow (Google + GitHub) fully tested via monkeypatched service stubs — works in any environment
- Argon2id password hashing with vault pepper; password change atomically revokes all other sessions
- Full 178-test suite passes with no regressions across vault, IAM, and auth

## Files Verified (pre-existing, no changes needed)

| File | Status | Purpose |
|------|--------|---------|
| `backend/01_core/middleware.py` | Verified complete | Session middleware: token extraction → vault validate → request.state injection |
| `backend/02_features/03_iam/feature.manifest.yaml` | Verified complete | iam.credentials, iam.sessions, iam.auth sub-features + 4 effect/request nodes |
| `backend/02_features/03_iam/routes.py` | Verified complete | Composes all 10 sub-feature routers including 08, 09, 10 |
| `backend/02_features/03_iam/sub_features/08_credentials/` | Verified complete | Argon2id password CRUD; PATCH /v1/credentials/me revokes sibling sessions |
| `backend/02_features/03_iam/sub_features/09_sessions/` | Verified complete | Session list/get/extend/revoke; validate_token reads vault signing key |
| `backend/02_features/03_iam/sub_features/10_auth/` | Verified complete | Signup/signin/signout/me/Google/GitHub; nodes: signup, signin, validate_session, revoke_session |
| `tests/test_iam_auth_api.py` | Verified passing | 8 tests: core auth flow + audit emission |
| `tests/test_iam_credentials_sessions_api.py` | Verified passing | 12 tests: credentials self-service + session management |
| `tests/test_iam_auth_oauth.py` | Verified passing | 6 tests: OAuth happy paths + collision + single-tenant default-org attach |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| OAuth tests use monkeypatching, not skip guards | Tests already stub `_exchange_google`/`_exchange_github` at service level — all downstream logic tested without real creds | No pytest.mark.skipif needed; 6/6 pass in any environment |
| Session middleware silently skips if vault absent | `vault is not None` guard — ensures clean startup even if vault module disabled | Matches existing vault-optional architecture |

## Deviations from Plan

None — plan executed exactly as written. All wiring was already correct; zero fixes required.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- Auth backend complete and tested end-to-end
- Session middleware wired — protected routes can guard via `request.state.user_id`
- Frontend auth pages exist (signin/signup/callback) — ready for verification in 08-02
- Topbar has user display code — needs browser verification
- All untracked files from phases 4-9 ready for the full commit in 08-02

**Concerns:**
- Large batch of uncommitted files (phases 4-9 backend + auth frontend + tests) — commit in 08-02 is critical

**Blockers:** None

---
*Phase: 08-auth, Plan: 01*
*Completed: 2026-04-16*
