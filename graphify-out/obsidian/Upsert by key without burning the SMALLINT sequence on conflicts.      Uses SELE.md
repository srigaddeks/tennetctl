---
source_file: "backend/01_catalog/repository.py"
type: "rationale"
community: "Audit Emit Pipeline"
location: "L67"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Emit_Pipeline
---

# Upsert by key without burning the SMALLINT sequence on conflicts.      Uses SELE

## Connections
- [[upsert_feature()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Emit_Pipeline