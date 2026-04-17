---
source_file: "backend/01_catalog/repository.py"
type: "rationale"
community: "Audit Emit Pipeline"
location: "L148"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Emit_Pipeline
---

# Upsert by key without burning the SMALLINT sequence on conflicts.

## Connections
- [[upsert_node()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Emit_Pipeline