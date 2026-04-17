---
source_file: "backend/02_features/05_monitoring/instrumentation/asyncpg.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L147"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Attach query loggers to all current + future pool connections.      asyncpg.Pool

## Connections
- [[install()_1]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ