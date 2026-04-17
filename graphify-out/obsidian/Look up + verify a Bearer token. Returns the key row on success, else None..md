---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L124"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Look up + verify a Bearer token. Returns the key row on success, else None.

## Connections
- [[register_complete()]] - `rationale_for` [EXTRACTED]
- [[validate_token()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware