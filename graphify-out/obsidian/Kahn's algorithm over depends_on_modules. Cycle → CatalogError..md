---
source_file: "backend/01_catalog/loader.py"
type: "rationale"
community: "Audit Emit Pipeline"
location: "L117"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Emit_Pipeline
---

# Kahn's algorithm over depends_on_modules. Cycle → CatalogError.

## Connections
- [[_topsort()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Emit_Pipeline