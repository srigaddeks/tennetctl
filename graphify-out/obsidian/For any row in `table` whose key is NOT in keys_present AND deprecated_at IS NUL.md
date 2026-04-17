---
source_file: "backend/01_catalog/repository.py"
type: "rationale"
community: "Audit Emit Pipeline"
location: "L190"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Emit_Pipeline
---

# For any row in `table` whose key is NOT in keys_present AND deprecated_at IS NUL

## Connections
- [[mark_absent_deprecated()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Emit_Pipeline