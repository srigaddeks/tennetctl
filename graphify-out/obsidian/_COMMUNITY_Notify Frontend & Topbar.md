---
type: community
cohesion: 0.18
members: 14
---

# Notify Frontend & Topbar

**Cohesion:** 0.18 - loosely connected
**Members:** 14 nodes

## Members
- [[API endpoint v1notifydeliveries]] - code - frontend/src/features/notify/hooks/use-in-app-notifications.ts
- [[API endpoint v1notifyunread-count]] - code - frontend/src/features/notify/hooks/use-in-app-notifications.ts
- [[API endpoint v1notifywebpushsubscriptions]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[API endpoint v1notifywebpushvapid-public-key]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[InAppDelivery type (status_code, priority_code, resolved_variables, deep_link)]] - code - frontend/src/features/notify/_components/notification-list.tsx
- [[NotificationBell component]] - code - frontend/src/features/notify/_components/notification-bell.tsx
- [[NotificationList + CriticalBanner components]] - code - frontend/src/features/notify/_components/notification-list.tsx
- [[WebPushSubscription type (id, org_id, user_id, endpoint, device_label)]] - code - frontend/src/features/notify/hooks/use-webpush.ts
- [[async()_1]] - code - frontend/src/components/topbar.tsx
- [[notification-bell.tsx]] - code - frontend/src/features/notify/_components/notification-bell.tsx
- [[topbar.tsx]] - code - frontend/src/components/topbar.tsx
- [[use-deliveries hook (useDeliveries)]] - code - frontend/src/features/notify/hooks/use-deliveries.ts
- [[use-in-app-notifications hooks (useInAppNotifications, useUnreadCount, useMarkRead, useMarkAllRead, useUnreadCountServer)]] - code - frontend/src/features/notify/hooks/use-in-app-notifications.ts
- [[use-webpush hooks (useWebPushSubscriptions, useEnableWebPush, useDisableWebPush)]] - code - frontend/src/features/notify/hooks/use-webpush.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Notify_Frontend_&_Topbar
SORT file.name ASC
```
