---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L70"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Create a key; return the sanitized row with `token` attached exactly once.

## Connections
- [[mint_api_key()]] - `rationale_for` [EXTRACTED]
- [[register_begin()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware