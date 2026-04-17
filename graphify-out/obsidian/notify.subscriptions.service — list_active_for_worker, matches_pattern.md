---
source_file: "backend/02_features/06_notify/sub_features/05_subscriptions/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.subscriptions.service — list_active_for_worker, matches_pattern

## Connections
- [[Concept event_key wildcard pattern matching (exact, prefix., )]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `conceptually_related_to` [INFERRED]
- [[notify.preferences.service — is_opted_in (channel+category opt-out check)]] - `conceptually_related_to` [INFERRED]
- [[notify.subscriptions repository — asyncpg raw SQL, v_notify_subscriptions]] - `calls` [EXTRACTED]
- [[notify.subscriptions routes — v1notifysubscriptions CRUD]] - `calls` [EXTRACTED]
- [[notify.templates.repository — get_template (used by worker to resolve template)]] - `shares_data_with` [INFERRED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization