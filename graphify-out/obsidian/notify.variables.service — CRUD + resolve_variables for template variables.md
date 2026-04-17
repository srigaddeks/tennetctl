---
source_file: "backend/02_features/06_notify/sub_features/04_variables/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.variables.service — CRUD + resolve_variables for template variables

## Connections
- [[backend.01_catalog.repository — raw asyncpg upserts into 01_catalog fct tables]] - `calls` [EXTRACTED]
- [[notify.routes — Feature router aggregating all notify sub-feature routers]] - `references` [INFERRED]
- [[notify.variables.repository — resolve_variables (used by worker to render template vars)]] - `calls` [EXTRACTED]
- [[notify.variables.schemas — TemplateVariableCreate  TemplateVariableUpdate  ResolveRequest  TemplateVariableRow]] - `shares_data_with` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization