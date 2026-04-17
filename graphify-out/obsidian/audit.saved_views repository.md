---
source_file: "backend/02_features/04_audit/sub_features/02_saved_views/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# audit.saved_views repository

## Connections
- [[DB table 10_fct_audit_saved_views]] - `references` [EXTRACTED]
- [[DB table 20_dtl_audit_saved_view_details]] - `references` [EXTRACTED]
- [[DB view v_audit_saved_views]] - `references` [EXTRACTED]
- [[core id (uuid7 generator)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature