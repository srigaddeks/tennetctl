---
source_file: "backend/02_features/04_audit/sub_features/03_outbox/repository.py"
type: "rationale"
community: "Audit Outbox"
location: "L54"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Outbox
---

# Return the current max outbox id (0 if empty). Used to initialise cursors.

## Connections
- [[latest_outbox_id()]] - `rationale_for` [EXTRACTED]
- [[reset_dim_cache()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Outbox