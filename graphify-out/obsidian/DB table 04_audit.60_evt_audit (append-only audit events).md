---
source_file: "backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py"
type: "document"
community: "Alert Rules & Evaluation"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# DB table: 04_audit.60_evt_audit (append-only audit events)

## Connections
- [[audit.events asyncpg repository (cursor pagination, stats, funnel, retention, upsert_event_key)]] - `references` [EXTRACTED]
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation