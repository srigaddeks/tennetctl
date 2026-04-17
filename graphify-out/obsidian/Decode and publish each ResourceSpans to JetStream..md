---
source_file: "backend/02_features/05_monitoring/sub_features/03_traces/service.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L53"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Decode and publish each ResourceSpans to JetStream.

## Connections
- [[create_org()]] - `rationale_for` [EXTRACTED]
- [[publish_traces_batch()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ