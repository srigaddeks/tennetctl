---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/repository.py"
type: "code"
community: "Session Auth & Middleware"
location: "L24"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# get_active_by_key_id()

## Connections
- [[Used by the Bearer middleware. Includes secret_hash for argon2 verify.]] - `rationale_for` [EXTRACTED]
- [[repository.py_14]] - `contains` [EXTRACTED]
- [[validate_token()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Session_Auth_&_Middleware