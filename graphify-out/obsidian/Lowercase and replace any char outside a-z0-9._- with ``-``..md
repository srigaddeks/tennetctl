---
source_file: "backend/02_features/05_monitoring/sub_features/01_logs/otlp_decoder.py"
type: "rationale"
community: "Admin Routes & DLQ"
location: "L31"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Admin_Routes_&_DLQ
---

# Lowercase and replace any char outside [a-z0-9._-] with ``-``.

## Connections
- [[_slugify_service_name()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Admin_Routes_&_DLQ