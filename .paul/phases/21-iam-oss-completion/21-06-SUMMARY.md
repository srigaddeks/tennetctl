---
phase: 21-iam-oss-completion
plan: 06
status: complete
---

# Plan 21-06 Summary: Session Management UI + OSS Docs

## What Was Done

- **`/account/sessions` page** — lists active sessions with created_at, last_activity, revoke per session, "sign out all other devices" button. Current session highlighted.
- **`use-sessions.ts` hook** — `useSessions()`, `useRevokeSession()`, `useRevokeAllOtherSessions()` with 15s refetch interval.
- **`session-row.tsx` component** — session row with Badge (tone-based), revoke button.
- **`SessionReadShape` type** in `frontend/src/types/api.ts`
- **OSS docs written**:
  - `SECURITY.md` — responsible disclosure, supported versions, GitHub Security Advisories
  - `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
  - `CONTRIBUTING.md` — dev setup, workflow, testing, PR process
