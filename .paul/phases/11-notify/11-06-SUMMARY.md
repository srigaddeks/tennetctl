---
phase: 11-notify
plan: 06
type: summary
status: complete
---

# Summary — Plan 11-06: In-App Notifications + Bell UI

## What Was Built

### Backend (delivery sub-feature extended)
- `service.py` — added `mark_in_app_read(conn, *, delivery_id, user_id)`:
  - Validates delivery exists, is channel=in_app, and caller is recipient
  - Idempotent: already-opened (status≥5) deliveries return current state without new event
  - Creates 'open' delivery event + advances status to 5 (opened)
  - Raises: NotFoundError, ValidationError (channel), ForbiddenError (wrong user)
- `routes.py` — added `PATCH /v1/notify/deliveries/{delivery_id}`:
  - Requires authentication (401 if no session)
  - Only `status: "opened"` supported (422 for other values)
  - Delegates to `mark_in_app_read`
- `feature.manifest.yaml` — added PATCH route to deliveries sub-feature 6

### Frontend
- `frontend/src/types/api.ts` — added `InAppDelivery`, `InAppDeliveryListResponse`, `DeliveryStatusCode`, `DeliveryPriorityCode`
- `frontend/src/lib/use-on-click-outside.ts` — utility hook for click-outside detection (popover dismiss)
- `frontend/src/features/notify/hooks/use-in-app-notifications.ts`:
  - `useInAppNotifications(userId, orgId)` — queries `/v1/notify/deliveries?channel=in_app`, polls 30s
  - `useUnreadCount(userId, orgId)` — derived count of not-yet-opened deliveries
  - `useMarkRead()` — PATCH mutation, invalidates notification list
  - `useMarkAllRead(userId, orgId)` — batch mark-read via `Promise.allSettled`
- `frontend/src/features/notify/_components/notification-list.tsx`:
  - `NotificationList` — scrollable list with per-item "Mark read" button; shows unread dot
  - `CriticalBanner` — persistent red banner for unread critical-priority in-app notifications; dismissible
- `frontend/src/features/notify/_components/notification-bell.tsx`:
  - Bell icon with unread count badge (0-99, "99+" when overflow)
  - Click-to-open popover with `NotificationList`; dismisses on click-outside
- `frontend/src/components/topbar.tsx`:
  - Wraps in `<>` fragment to render `CriticalBanner` above the header
  - `NotificationBell` inserted in topbar right section when user is authenticated
  - `useInAppNotifications` called at topbar level; items passed to both `CriticalBanner` and `NotificationBell`

## Test Results

9/9 tests green (`tests/test_notify_deliveries_patch.py`):
- Service (5): mark-read advances to opened + event, idempotent, forbidden for wrong user, channel guard, not-found
- HTTP (4): auth guard (401), unsupported status (422), mark-read via HTTP, list channel filter

TypeScript: clean compile (no errors).

## Key Decisions Made

1. **PATCH on existing deliveries route** — `mark_in_app_read` added to existing `06_deliveries` sub-feature; no new sub-feature needed for this write path. The in-app *sender* sub-feature is not needed because in-app delivery status advances happen client-side (user reads it).
2. **Idempotent by status_id≥5** — avoiding second event creation when `mark_in_app_read` called twice; simpler than tracking event existence.
3. **CriticalBanner above header** — uses `<>` fragment wrapper in TopBar to render the sticky banner above the nav without affecting layout.
4. **30s polling vs WebSocket** — simple polling sufficient for MVP; real-time (LISTEN/NOTIFY) deferred to later.
5. **useUnreadCount as derived value** — computed from existing notification list query; no separate unread-count API endpoint needed.

## Files Created/Modified

**Created:**
- `frontend/src/lib/use-on-click-outside.ts`
- `frontend/src/features/notify/hooks/use-in-app-notifications.ts`
- `frontend/src/features/notify/_components/notification-list.tsx`
- `frontend/src/features/notify/_components/notification-bell.tsx`
- `tests/test_notify_deliveries_patch.py`

**Modified:**
- `backend/02_features/06_notify/sub_features/06_deliveries/service.py` (mark_in_app_read)
- `backend/02_features/06_notify/sub_features/06_deliveries/routes.py` (PATCH route)
- `backend/02_features/06_notify/feature.manifest.yaml` (PATCH in deliveries sub-feature)
- `frontend/src/types/api.ts` (InAppDelivery types)
- `frontend/src/components/topbar.tsx` (CriticalBanner + NotificationBell)
