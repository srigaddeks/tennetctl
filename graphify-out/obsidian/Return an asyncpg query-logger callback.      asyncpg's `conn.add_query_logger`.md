---
source_file: "backend/02_features/05_monitoring/instrumentation/asyncpg.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L104"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Return an asyncpg query-logger callback.      asyncpg's `conn.add_query_logger`

## Connections
- [[make_query_logger()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ