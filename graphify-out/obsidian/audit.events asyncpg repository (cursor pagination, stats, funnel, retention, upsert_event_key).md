---
source_file: "backend/02_features/04_audit/sub_features/01_events/repository.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# audit.events asyncpg repository (cursor pagination, stats, funnel, retention, upsert_event_key)

## Connections
- [[DB table 04_audit.60_evt_audit (append-only audit events)]] - `references` [EXTRACTED]
- [[DB view 04_audit.v_audit_events (joins dim_audit_categories + dim_audit_event_keys)]] - `references` [EXTRACTED]
- [[audit.events service (read path query, get, stats, funnel, retention, list_keys)]] - `calls` [EXTRACTED]
- [[node audit.events.query (control node — read-only cursor-paginated event lookup)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation