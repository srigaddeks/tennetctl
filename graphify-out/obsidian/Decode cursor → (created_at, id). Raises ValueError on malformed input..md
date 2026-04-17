---
source_file: "backend/02_features/04_audit/sub_features/01_events/repository.py"
type: "rationale"
community: "Audit Events & Saved Views"
location: "L36"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Events_&_Saved_Views
---

# Decode cursor → (created_at, id). Raises ValueError on malformed input.

## Connections
- [[_decode_cursor()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Events_&_Saved_Views