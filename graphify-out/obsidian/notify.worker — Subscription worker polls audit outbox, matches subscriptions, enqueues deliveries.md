---
source_file: "backend/02_features/06_notify/worker.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.worker — Subscription worker: polls audit outbox, matches subscriptions, enqueues deliveries

## Connections
- [[audit.outbox.repository — poll_outbox, latest_outbox_id (used by notify worker)]] - `calls` [EXTRACTED]
- [[notify.deliveries.service — create_delivery]] - `calls` [EXTRACTED]
- [[notify.preferences.service — is_opted_in (channel+category opt-out check)]] - `calls` [EXTRACTED]
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - `calls` [EXTRACTED]
- [[notify.templates.repository — get_template (used by worker to resolve template)]] - `calls` [EXTRACTED]
- [[notify.variables.repository — resolve_variables (used by worker to render template vars)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization