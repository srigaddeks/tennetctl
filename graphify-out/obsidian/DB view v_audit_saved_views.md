---
source_file: "backend/02_features/04_audit/sub_features/02_saved_views/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/API_Keys_Sub-feature
---

# DB view: v_audit_saved_views

## Connections
- [[DB table 10_fct_audit_saved_views]] - `references` [INFERRED]
- [[DB table 20_dtl_audit_saved_view_details]] - `references` [INFERRED]
- [[audit.saved_views repository]] - `references` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/API_Keys_Sub-feature