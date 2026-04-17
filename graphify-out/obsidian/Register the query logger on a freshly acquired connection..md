---
source_file: "backend/02_features/05_monitoring/instrumentation/asyncpg.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L139"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Register the query logger on a freshly acquired connection.

## Connections
- [[_attach_to_conn()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ