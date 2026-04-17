---
source_file: "backend/02_features/04_audit/sub_features/02_saved_views/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Alert_Rules_&_Evaluation
---

# audit.saved_views service (list/create/delete saved views)

## Connections
- [[audit feature router (aggregates events + saved_views sub-routers)]] - `calls` [INFERRED]
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - `conceptually_related_to` [INFERRED]
- [[audit.saved_views Pydantic schemas (AuditSavedViewCreate, AuditSavedViewRow)]] - `references` [INFERRED]

#graphify/code #graphify/INFERRED #community/Alert_Rules_&_Evaluation