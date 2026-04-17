---
source_file: "backend/01_catalog/repository.py"
type: "code"
community: "Audit Emit Pipeline"
location: "L184"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Audit_Emit_Pipeline
---

# mark_absent_deprecated()

## Connections
- [[For any row in `table` whose key is NOT in keys_present AND deprecated_at IS NUL]] - `rationale_for` [EXTRACTED]
- [[ValueError]] - `calls` [INFERRED]
- [[repository.py]] - `contains` [EXTRACTED]
- [[upsert_all()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Audit_Emit_Pipeline