---
source_file: "backend/02_features/04_audit/sub_features/01_events/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)

## Connections
- [[audit feature router (aggregates events + saved_views sub-routers)]] - `calls` [EXTRACTED]
- [[audit outbox service (current_cursor, poll)]] - `calls` [EXTRACTED]
- [[audit.events Pydantic schemas (AuditEventFilter, AuditEventRow, FunnelRequest, RetentionResponse)]] - `references` [EXTRACTED]
- [[audit.events service (read path query, get, stats, funnel, retention, list_keys)]] - `calls` [EXTRACTED]
- [[audit.saved_views service (listcreatedelete saved views)]] - `conceptually_related_to` [INFERRED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation