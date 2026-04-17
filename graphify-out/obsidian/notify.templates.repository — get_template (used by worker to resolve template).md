---
source_file: "backend/02_features/06_notify/sub_features/03_templates/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Error_Types_&_Authorization
---

# notify.templates.repository — get_template (used by worker to resolve template)

## Connections
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - `shares_data_with` [INFERRED]
- [[notify.template_groups.schemas — TemplateGroupCreate  TemplateGroupUpdate  TemplateGroupRow]] - `conceptually_related_to` [INFERRED]
- [[notify.template_groups.service — CRUD + audit emission for template groups]] - `conceptually_related_to` [INFERRED]
- [[notify.variables.repository — resolve_variables (used by worker to render template vars)]] - `shares_data_with` [INFERRED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Error_Types_&_Authorization