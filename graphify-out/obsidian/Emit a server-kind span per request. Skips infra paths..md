---
source_file: "backend/02_features/05_monitoring/instrumentation/fastapi.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L134"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Emit a server-kind span per request. Skips infra paths.

## Connections
- [[MonitoringMiddleware]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ