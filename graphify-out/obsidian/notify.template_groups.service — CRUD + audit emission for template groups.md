---
source_file: "backend/02_features/06_notify/sub_features/02_template_groups/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.template_groups.service — CRUD + audit emission for template groups

## Connections
- [[backend.01_catalog.repository — raw asyncpg upserts into 01_catalog fct tables]] - `calls` [EXTRACTED]
- [[notify.template_groups.repository — asyncpg CRUD on 06_notify.11_fct_notify_template_groups]] - `calls` [EXTRACTED]
- [[notify.template_groups.routes — REST API v1notifytemplate-groups]] - `calls` [EXTRACTED]
- [[notify.templates.repository — get_template (used by worker to resolve template)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization