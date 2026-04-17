---
phase: 21-iam-oss-completion
plan: 04
status: complete
---

# 21-04 Summary — Deactivation vs Soft-Delete for Users

## What was built

Introduced a clear distinction between reversible deactivation and one-way
soft-delete/pseudonymization for users.

## Changes

### Backend

**`backend/02_features/03_iam/sub_features/03_users/service.py`**
- Added `deactivate_user()` — sets `is_active=False`, revokes all active sessions via
  `sessions.repository.revoke_all_for_user`, emits `iam.users.deactivated`.
- Added `reactivate_user()` — sets `is_active=True`, emits `iam.users.reactivated`.
- Rewrote `delete_user()` → now pseudonymizes email (`deleted-{uuid7}@removed.local`),
  display_name (`[deleted user]`), clears avatar_url, revokes sessions, sets `deleted_at`,
  emits `iam.users.deleted` with `original_email_hash` (SHA-256) and `pseudonymized_email`.
- Updated `update_user()` to route `status="active"/"inactive"` to the appropriate
  specific function. Deprecated `is_active` bool kept for backward compat.

**`backend/02_features/03_iam/sub_features/03_users/schemas.py`**
- Added `status: Literal["active", "inactive"] | None` to `UserUpdate`.
- Kept `is_active: bool | None` for backward compat (deprecated).

**`backend/02_features/03_iam/sub_features/03_users/routes.py`**
- Passes `status=body.status` to `update_user`.

**`backend/02_features/03_iam/sub_features/10_auth/service.py`**
- Split `user is None or not user["is_active"]` check into two separate branches.
- Inactive user now raises `ForbiddenError("account is deactivated", code="USER_INACTIVE")`
  (HTTP 403) instead of the generic 401.

### Frontend

**`frontend/src/types/api.ts`**
- Added `status?: "active" | "inactive"` to `UserUpdateBody`.

**`frontend/src/app/(dashboard)/iam/users/[id]/page.tsx`** (new file)
- User detail page with status badge (Active/Inactive), Deactivate/Reactivate button,
  and Delete button.
- Deactivate/Reactivate shows confirmation modal.
- Delete shows modal requiring user to type the email address to unlock the confirm button
  (GDPR safeguard).

### Tests

**`tests/test_iam_user_lifecycle.py`** (new file, 6 tests — all green)
- `test_deactivate_user_via_status` — PATCH status=inactive sets is_active=False + audit
- `test_reactivate_user_via_status` — PATCH status=active after deactivation
- `test_list_filter_by_is_active` — deactivated user appears in ?is_active=false
- `test_delete_pseudonymizes_user` — email pseudonymized, deleted_at set, GET returns 404
- `test_inactive_user_cannot_get_via_list_active_filter`
- `test_no_op_when_status_unchanged` — no audit events when status doesn't change

**`tests/e2e/iam/24_deactivate_vs_delete.robot`** (new file)
- Robot E2E covering deactivate-blocks-signin, reactivate-restores-access,
  delete-pseudonymizes, frontend status badge, and delete confirm modal.

## AC coverage

| AC | Status |
|----|--------|
| AC-1: is_active in v_users | Pre-existing (boolean column on fct_users) |
| AC-2: PATCH status=inactive deactivates | Done |
| AC-3: PATCH status=active reactivates | Done |
| AC-4: DELETE pseudonymizes + soft-deletes | Done |
| AC-5: Frontend detail page | Done |
| AC-6: Tests + Robot E2E | Done |

## Key decisions

- `is_active` stays as a boolean column on `fct_users` (already existed, not EAV).
  The EAV migration described in the plan was not needed — the column is already there.
- Deactivation uses the existing `update_active` repo function. No new DB columns needed.
- Auth returns distinct 403 `USER_INACTIVE` for inactive users vs 401 for unknown users.
