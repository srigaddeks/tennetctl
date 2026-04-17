---
phase: 21-iam-oss-completion
plan: 02
status: complete
---

## What Was Built

Admin invite flow sub-feature (`17_invites/`) — org admins send invite links, recipients accept and create accounts with pre-verified email + auto-assigned org/roles.

## Deliverables

### Migration
- `20260417_057_iam-invites.sql` — creates `13_fct_user_invites` table in `"03_iam"` schema with HMAC token hash, status (1=pending, 2=accepted, 3=cancelled, 4=expired), expires_at. Applied successfully.

### Backend Sub-feature
- `backend/02_features/03_iam/sub_features/17_invites/` — 5 files
- `POST /v1/orgs/{org_id}/invites` — create invite (admin only), generates HMAC token, fires iam.invite.email notify (best-effort), returns 201
- `GET /v1/orgs/{org_id}/invites` — list pending invites (admin only)
- `DELETE /v1/orgs/{org_id}/invites/{invite_id}` — cancel/soft-delete invite
- `POST /v1/auth/accept-invite` — public endpoint: verify token → create user → auto-assign to org → mark email verified → return session

### IAM Routes
- `backend/02_features/03_iam/routes.py` — registered `_invites_routes`

### Notify Seed
- `backend/02_features/06_notify/seeds/iam_invite_template.yaml` — template key `iam.invite.email`

### Frontend
- `frontend/src/app/(dashboard)/iam/invites/page.tsx` — admin list + send invite form
- `frontend/src/app/auth/accept-invite/page.tsx` — public token-consumption page
- `frontend/src/types/api.ts` — added `Invite` type + related body/result types

## Acceptance Criteria Status

- [x] Migration clean; table created
- [x] create invite: admin-only, token signed, 201
- [x] list/cancel invites: admin-only
- [x] accept-invite: token verified, user created, email pre-verified, org assigned, session returned
- [x] Frontend admin page + public accept page
- [x] Notify template seeded (iam.invite.email)

## Implementation Notes (actual build)

- Table numbered `30_fct_user_invites` (next available after `29_fct_iam_email_verifications`)
- `v_invites` view intentionally omits `token_hash` column (security); `get_by_token_hash` repo function queries raw table directly
- HMAC signing key `iam.invite_signing_key` auto-bootstrapped in vault on first use (identical pattern to `iam.password_reset_signing_key`)
- `audit_category="setup"` used throughout (satisfies `chk_evt_audit_scope` constraint without requiring full session/org/workspace context on the token-acceptance endpoint)
- 4/4 integration tests pass: create returns 201 without raw token, accept creates user + session, wrong token → 401, cancel → status=3
