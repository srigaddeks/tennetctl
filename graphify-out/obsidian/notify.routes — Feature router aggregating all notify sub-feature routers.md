---
source_file: "backend/02_features/06_notify/routes.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.routes — Feature router aggregating all notify sub-feature routers

## Connections
- [[notify.suppression.routes — v1notifysuppressions (admin) + v1notifyunsubscribe (public RFC 8058)]] - `references` [EXTRACTED]
- [[notify.template_groups.routes — REST API v1notifytemplate-groups]] - `references` [EXTRACTED]
- [[notify.variables.service — CRUD + resolve_variables for template variables]] - `references` [INFERRED]
- [[notify.webpush.routes — v1notifywebpushvapid-public-key + v1notifywebpushsubscriptions]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization