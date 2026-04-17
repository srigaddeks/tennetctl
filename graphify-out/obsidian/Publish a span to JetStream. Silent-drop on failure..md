---
source_file: "backend/02_features/05_monitoring/instrumentation/fastapi.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L183"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Publish a span to JetStream. Silent-drop on failure.

## Connections
- [[_publish_span()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ