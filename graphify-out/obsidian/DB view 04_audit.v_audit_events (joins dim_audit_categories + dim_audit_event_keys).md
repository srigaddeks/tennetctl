---
source_file: "backend/02_features/04_audit/sub_features/01_events/repository.py"
type: "document"
community: "Alert Rules & Evaluation"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# DB view: 04_audit.v_audit_events (joins dim_audit_categories + dim_audit_event_keys)

## Connections
- [[audit.events asyncpg repository (cursor pagination, stats, funnel, retention, upsert_event_key)]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation