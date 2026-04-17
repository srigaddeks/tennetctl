---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/repository.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L25"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Used by the Bearer middleware. Includes secret_hash for argon2 verify.

## Connections
- [[get_active_by_key_id()]] - `rationale_for` [EXTRACTED]
- [[get_subscription()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware