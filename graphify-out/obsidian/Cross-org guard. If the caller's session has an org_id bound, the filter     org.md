---
source_file: "backend/02_features/04_audit/sub_features/01_events/routes.py"
type: "rationale"
community: "Audit Events & Saved Views"
location: "L96"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Events_&_Saved_Views
---

# Cross-org guard. If the caller's session has an org_id bound, the filter     org

## Connections
- [[_enforce_org_authz()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Events_&_Saved_Views