---
source_file: "backend/02_features/06_notify/sub_features/09_preferences/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.preferences.service — is_opted_in (channel+category opt-out check)

## Connections
- [[Concept critical notification category cannot be opted out]] - `implements` [EXTRACTED]
- [[notify.preferences repository — upsertget_opt_in, 17_fct_notify_user_preferences]] - `calls` [EXTRACTED]
- [[notify.preferences routes — GETPATCH v1notifypreferences]] - `calls` [EXTRACTED]
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - `conceptually_related_to` [INFERRED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization