---
source_file: "backend/02_features/04_audit/sub_features/01_events/repository.py"
type: "rationale"
community: "Audit Events & Saved Views"
location: "L442"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Events_&_Saved_Views
---

# Idempotent upsert for auto-sync of observed event keys. Resolves category_code

## Connections
- [[upsert_event_key()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Events_&_Saved_Views