---
source_file: "backend/02_features/06_notify/sub_features/01_smtp_configs/routes.py"
type: "rationale"
community: "API Routes & Response Handling"
location: "L30"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/API_Routes_&_Response_Handling
---

# SMTP config mutations are org-level config (no workspace scope);     audit_categ

## Connections
- [[_build_ctx()]] - `rationale_for` [EXTRACTED]
- [[_require_auth()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/API_Routes_&_Response_Handling