---
source_file: "frontend/src/app/(dashboard)/notify/preferences/page.tsx"
type: "code"
community: "API Endpoint Type Catalog"
location: "line 64"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Endpoint_Type_Catalog
---

# NotificationPreferencesPage — channel/category opt-in matrix

## Connections
- [[BrowserPushSection — VAPID web push enabledisable UI]] - `calls` [EXTRACTED]
- [[NotifyPreference — user channelcategory opt-in]] - `shares_data_with` [EXTRACTED]
- [[use-notify-preferences hook — fetch + update user preferences]] - `calls` [EXTRACTED]
- [[use-webpush hooks — browser push enabledisablesubscriptions]] - `calls` [EXTRACTED]
- [[useMe — hook returning current user + session]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Endpoint_Type_Catalog