---
phase: 38-auth-hardening
plan: 38-02
subsystem: auth
tags: [session-rotation, mfa, password-change, session-fixation, iam]

requires:
  - phase: 38-auth-hardening
    provides: rotate_on_login helper, session-fixation defense on login (38-01)
  - phase: 20-iam-hardening-for-oss
    provides: change_password flow + TOTP setup flow (20-0x series)

provides:
  - rotate_on_privilege_escalation() — mint+revoke+audit helper for post-auth boundaries
  - Password-change response carries new session cookie (breaking-compatible body extension)
  - TOTP setup response carries new session cookie (breaking-compatible body extension)

affects: [future passkey-enroll rotation, SDK auth clients if they care about rotated cookies]

tech-stack:
  added: []
  patterns:
    - Dual rotation helpers: rotate_on_login (revoke-only, new already minted)
      + rotate_on_privilege_escalation (mint+revoke+audit)

key-files:
  modified:
    - backend/02_features/03_iam/sub_features/09_sessions/service.py
    - backend/02_features/03_iam/sub_features/08_credentials/{service,routes}.py
    - backend/02_features/03_iam/sub_features/12_otp/{service,routes}.py

key-decisions:
  - "Two rotation helpers coexist: rotate_on_login (38-01) + rotate_on_privilege_escalation (38-02). Full consolidation deferred — login path untouched per boundary."
  - "TOTP rotation wired to setup_totp, not a phantom 'confirm' endpoint — setup IS the enrollment in this codebase"
  - "change_password return shape extended from int → (int, str|None, dict|None). Tuple unpack is backward-incompatible for any internal caller; confirmed only the HTTP route calls this function"
  - "Rotation failure swallowed; password-change / TOTP setup itself still succeeds with old session intact"

patterns-established:
  - "Post-auth rotation pattern: service takes previous_session_id + vault_client + scope; returns (new_token, new_session); route re-sets cookie on response when present"

duration: ~25min
started: 2026-04-20T20:30:00Z
completed: 2026-04-20T20:55:00Z
---

# Phase 38 Plan 02: Password-change + MFA-enroll Rotation Summary

**AC-1 of the original 38-01 plan now fully satisfied — session rotates on all three OWASP privilege-escalation boundaries (login, password-change, MFA-enrollment).**

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Session rotation on password change | PASS | Rotates, revokes with reason="rotated_on_password_change", audits, carries new cookie |
| AC-2: Session rotation on TOTP enrollment | PASS (spec pivot) | Rotated on `/totp/setup` (actual enrollment boundary) rather than a non-existent `/confirm` step. Same security outcome. |

## Accomplishments

- **Generalized rotation helper** — `rotate_on_privilege_escalation(... reason="...")` handles both password-change and MFA-enroll; new session inherits caller's scope, old session is revoked atomically, audit fires with structured metadata.
- **Password-change flow hardened** — PATCH /v1/credentials/me now returns a new session token + cookie; the old session_id (which predates the strengthened auth state) is revoked with reason tagged in `updated_by`.
- **TOTP enrollment flow hardened** — POST /v1/auth/totp/setup re-sets the session cookie on success; both `iam.otp.totp.enrolled` AND `iam.session.rotated{reason=mfa_enrolled}` fire.
- **Existing safety-net preserved** — change_password's "revoke all OTHER sessions" behavior from Plan 20-x is untouched; rotation is additional, not replacement.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `.../09_sessions/service.py` | Modified | Added `rotate_on_privilege_escalation()` (~55 LoC) |
| `.../08_credentials/service.py` | Modified | `change_password` accepts vault + scope; returns tuple; calls rotate helper |
| `.../08_credentials/routes.py` | Modified | Added cookie helpers; re-sets cookie + adds token/session to response body |
| `.../12_otp/service.py` | Modified | `setup_totp` accepts `previous_session_id` + scope; rotates post-audit |
| `.../12_otp/routes.py` | Modified | Sets new cookie when rotation produced a token |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Keep `rotate_on_login` alongside `rotate_on_privilege_escalation` | Boundary "DO NOT CHANGE signin path" — consolidating both helpers would touch signin code | Two helpers in 09_sessions; minor future cleanup item |
| Rotate at `setup_totp`, not a "confirm" endpoint | Codebase has no separate confirm step — setup persists credential + emits `iam.otp.totp.enrolled` inline | Same security outcome; plan naming was aspirational |
| Swallow rotation failure (return old `new_token=None`) | Rotation failing must not fail the password change or TOTP setup itself — those already succeeded before the rotate call | Caller gets old session back in the pathological rotation-failure case; audit still logs the failure via the helper's internal try/except |
| Tuple return shape on `change_password` | Only one caller (the HTTP route); a dict return would require boilerplate at the one call site | Clean; verified no other callers via grep |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Spec pivot | 1 | TOTP "confirm" endpoint doesn't exist; wired to setup_totp instead |
| Scope trim | 1 | Did not consolidate rotate_on_login into the new helper (boundary respected) |
| Plan-predicted feature already present | 0 | — |

**Total impact:** AC intent satisfied; no scope creep; boundaries honored.

### Spec Pivot

**TOTP has no separate confirm step** — Plan 38-02 assumed an endpoint like `POST /v1/auth/otp/totp/confirm` where the user enters the code after scanning to activate the credential. Reality: `POST /v1/auth/totp/setup` persists the credential + fires `iam.otp.totp.enrolled` immediately; `/totp/verify` is used for step-up verification during subsequent signins (not activation). Rotation wired to `setup_totp` — the actual boundary where the credential becomes live.

### Deferred Items

- Consolidate `rotate_on_login` as a thin wrapper around `rotate_on_privilege_escalation` (cosmetic cleanup; 38-01's boundary held it at arm's length)
- Passkey enrollment rotation (same boundary class, separate sub-feature — follow-up if needed)
- Live DB verification (operator-deferred per project pattern)

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Pyright return-type error after signature change | Updated return statement to yield the 3-tuple consistent with new annotation |
| Plan assumed `/totp/confirm` endpoint | Pivoted to `setup_totp` — same security boundary, different endpoint name |

## Next Phase Readiness

**Ready:**
- Phase 39 (NCP v1 Maturity) can proceed — auth hardening is substantively complete
- Any future passkey / email-verify rotation can reuse `rotate_on_privilege_escalation` directly

**Concerns:**
- The `iam.auth.rate_limited` event from 38-01 + `iam.session.rotated` events added here are NOT yet seeded in `dim_audit_event_keys`. The audit emit will auto-register them on first fire (comment in 04_audit/01_events/repository.py confirms dynamic registration), but security dashboards that expect pre-seeded taxonomy won't see them until first emit.
- SDK clients (Python/TS) do not know about the optional `token`/`session` keys in the change-password / setup-totp response bodies; they'll ignore them harmlessly, but picking up the rotated cookie requires the browser/client to honor Set-Cookie on non-auth endpoints (standard).

**Blockers:**
- None. Live DB verification remains operator-deferred.

---
*Phase: 38-auth-hardening, Plan: 02*
*Completed: 2026-04-20*
