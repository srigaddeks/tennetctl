---
type: community
cohesion: 0.06
members: 36
---

# API Endpoint Type Catalog

**Cohesion:** 0.06 - loosely connected
**Members:** 36 nodes

## Members
- [[AccountType — email_password  magic_link  google_oauth  github_oauth]] - code - frontend/src/types/api.ts
- [[AlertRule — monitoring alert rule]] - code - frontend/src/types/api.ts
- [[AuditEventRow — audit event record]] - code - frontend/src/types/api.ts
- [[AuthResponseBody — token + user + session]] - code - frontend/src/types/api.ts
- [[AuthSession — session shape with orgworkspace]] - code - frontend/src/types/api.ts
- [[BrowserPushSection — VAPID web push enabledisable UI]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[CatalogNode — node registry entry]] - code - frontend/src/types/api.ts
- [[DeliveriesPage — delivery list with statuschannel filters]] - code - frontend/src/app/(dashboard)/notify/deliveries/page.tsx
- [[GET v1catalognodes — node registry API endpoint]] - code - frontend/src/app/(dashboard)/nodes/page.tsx
- [[MagicLinkCallbackPage — consumes magic link token]] - code - frontend/src/app/auth/magic-link/callback/page.tsx
- [[NodesPage — live node catalog viewer from v1catalognodes]] - code - frontend/src/app/(dashboard)/nodes/page.tsx
- [[NotificationPreferencesPage — channelcategory opt-in matrix]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[NotifyDelivery — notification delivery record]] - code - frontend/src/types/api.ts
- [[NotifyPreference — user channelcategory opt-in]] - code - frontend/src/types/api.ts
- [[NotifySMTPConfig — SMTP server config type]] - code - frontend/src/types/api.ts
- [[NotifySettingsPage — SMTP configs + template groups + subscriptions]] - code - frontend/src/app/(dashboard)/notify/settings/page.tsx
- [[NotifySubscription — audit-event to notification trigger rule]] - code - frontend/src/types/api.ts
- [[NotifyTemplate — notification template type]] - code - frontend/src/types/api.ts
- [[NotifyTemplateVariable — static or dynamic_sql template variable]] - code - frontend/src/types/api.ts
- [[Org — IAM org type]] - code - frontend/src/types/api.ts
- [[POST v1authmagic-linkconsume — magic link token exchange]] - code - frontend/src/app/auth/magic-link/callback/page.tsx
- [[POST v1notifysend — transactional send API endpoint]] - code - frontend/src/app/(dashboard)/notify/send/page.tsx
- [[TemplateDesignerPage — multi-channel template editor + preview + analytics]] - code - frontend/src/app/(dashboard)/notify/templates/[id]/page.tsx
- [[TemplatesPage — list and create notification templates]] - code - frontend/src/app/(dashboard)/notify/templates/page.tsx
- [[TransactionalSendPage — direct notification send bypassing subscription flow]] - code - frontend/src/app/(dashboard)/notify/send/page.tsx
- [[User — IAM user type]] - code - frontend/src/types/api.ts
- [[VaultSecretMeta — vault secret metadata (no plaintext)]] - code - frontend/src/types/api.ts
- [[Workspace — IAM workspace type]] - code - frontend/src/types/api.ts
- [[apiFetch  apiList — typed HTTP client with ok-envelope check]] - code - frontend/src/app/(dashboard)/nodes/page.tsx
- [[use-deliveries hook — notify delivery list]] - code - frontend/src/app/(dashboard)/notify/deliveries/page.tsx
- [[use-notify-preferences hook — fetch + update user preferences]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[use-notify-settings hooks — SMTP configs, template groups, subscriptions]] - code - frontend/src/app/(dashboard)/notify/settings/page.tsx
- [[use-template-variables hooks — variable CRUD + resolve]] - code - frontend/src/app/(dashboard)/notify/templates/[id]/page.tsx
- [[use-templates hooks — template CRUD + analytics + test send]] - code - frontend/src/app/(dashboard)/notify/templates/page.tsx
- [[use-webpush hooks — browser push enabledisablesubscriptions]] - code - frontend/src/app/(dashboard)/notify/preferences/page.tsx
- [[useMe — hook returning current user + session]] - code - frontend/src/app/(dashboard)/notify/settings/page.tsx

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/API_Endpoint_Type_Catalog
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Error Types & Authorization]]

## Top bridge nodes
- [[TransactionalSendPage — direct notification send bypassing subscription flow]] - degree 4, connects to 1 community
- [[CatalogNode — node registry entry]] - degree 2, connects to 1 community