---
source_file: "backend/02_features/06_notify/sub_features/04_variables/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.variables.repository — resolve_variables (used by worker to render template vars)

## Connections
- [[notify.deliveries.service — create_delivery]] - `shares_data_with` [INFERRED]
- [[notify.templates.repository — get_template (used by worker to resolve template)]] - `shares_data_with` [INFERRED]
- [[notify.variables.service — CRUD + resolve_variables for template variables]] - `calls` [EXTRACTED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization