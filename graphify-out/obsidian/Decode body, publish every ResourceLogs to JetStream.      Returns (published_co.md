---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/service.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L47"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Decode body, publish every ResourceLogs to JetStream.      Returns (published_co

## Connections
- [[publish_logs_batch()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ