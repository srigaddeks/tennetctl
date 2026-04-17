---
phase: 11-notify
plan: 07
type: summary
status: complete
---

# Summary — Plan 11-07: User Preferences + Unsubscribe Flow

## What Was Built

### Database
- Migration 027: `17_fct_notify_user_preferences` — UNIQUE on (org_id, user_id, channel_id, category_id), FK to dim_notify_channels + dim_notify_categories, no deleted_at (idempotent upsert overwrites)
- View `v_notify_user_preferences` — joins resolved channel + category codes

### Backend sub-feature 09_preferences (5 files)
- `schemas.py` — `PreferencePatchItem`, `PreferencePatchBody`, `PreferenceRow` (with `is_locked` field)
- `repository.py`:
  - `list_preferences(conn, *, user_id, org_id)` — reads view
  - `upsert_preference(conn, *, ...)` — ON CONFLICT DO UPDATE
  - `get_opt_in(conn, *, user_id, org_id, channel_id, category_id)` — returns None if no row
- `service.py`:
  - `list_preferences()` — returns all 16 combos with defaults; critical always forced to True + is_locked=True
  - `upsert_preference()` — validates codes; silently forces critical to True
  - `is_opted_in()` — called by worker; returns True for critical, True for missing row, stored value otherwise
- `routes.py`:
  - `GET /v1/notify/preferences` — 16 rows, auth required
  - `PATCH /v1/notify/preferences` — batch upsert, auth required

### Worker update (worker.py)
- Imported `_pref_service`
- Before calling `create_delivery` for each channel, calls `is_opted_in()` for the recipient
- Skips delivery and logs debug when opted out; critical always passes through

### Manifest (feature.manifest.yaml)
- Added sub-feature `notify.preferences` (number 9) with GET + PATCH routes

### Routes aggregator (routes.py)
- Added `_preferences.router` inclusion

### Frontend
- `frontend/src/types/api.ts` — added `NotifyPreference`, `NotifyPreferencePatchItem`, `NotifyChannelCode`, `NotifyCategoryCode`
- `frontend/src/features/notify/hooks/use-notify-preferences.ts` — `useNotifyPreferences()` + `useUpdatePreferences()` TanStack Query hooks
- `frontend/src/app/(dashboard)/notify/preferences/page.tsx` — 4×4 toggle grid with:
  - Category rows with description text
  - Channel columns (Email, Web Push, In-App, SMS)
  - Toggle switch with optimistic update + rollback on error
  - Critical row disabled with "Always on" badge
  - Saving state per-cell
- `frontend/src/config/features.ts` — added `notify` feature nav with Preferences sub-feature link

## Test Results

15/15 tests green (`tests/test_notify_preferences_api.py`):
- Service (10): list defaults, list reflects stored, critical forced in list, upsert opt-out, upsert critical forced, unknown channel/category validation, is_opted_in default/stored/critical
- HTTP (5): GET auth guard, GET 16 rows, PATCH auth guard, PATCH updates, PATCH cannot opt out of critical

TypeScript: clean compile.

## Key Decisions Made

1. **16 combos returned regardless of stored rows** — service assembles full grid from embedded channel/category arrays; absence of a row = opted in. No N+1 DB queries.
2. **Critical forced silently, not rejected** — cleaner UX; server forces True, returns is_locked=True for client to disable the toggle. No error thrown.
3. **is_opted_in() short-circuits for critical** — zero DB hit for critical category in the worker hot path.
4. **Worker skips delivery on opt-out** — not an error; just a debug log + continue. Idempotency unaffected (delivery never created, so no conflict row either).
5. **Toggle page at /notify/preferences** — not under /settings since there's no settings section; notify owns its user preferences.

## Files Created/Modified

**Created:**
- `03_docs/features/06_notify/05_sub_features/09_preferences/09_sql_migrations/02_in_progress/20260417_027_notify-user-preferences.sql` (→ auto-moved to 01_migrated after apply)
- `backend/02_features/06_notify/sub_features/09_preferences/__init__.py`
- `backend/02_features/06_notify/sub_features/09_preferences/schemas.py`
- `backend/02_features/06_notify/sub_features/09_preferences/repository.py`
- `backend/02_features/06_notify/sub_features/09_preferences/service.py`
- `backend/02_features/06_notify/sub_features/09_preferences/routes.py`
- `frontend/src/features/notify/hooks/use-notify-preferences.ts`
- `frontend/src/app/(dashboard)/notify/preferences/page.tsx`
- `tests/test_notify_preferences_api.py`

**Modified:**
- `backend/02_features/06_notify/worker.py` (preference check before delivery creation)
- `backend/02_features/06_notify/routes.py` (include preferences router)
- `backend/02_features/06_notify/feature.manifest.yaml` (preferences sub-feature)
- `frontend/src/types/api.ts` (NotifyPreference types)
- `frontend/src/config/features.ts` (notify nav entry)
