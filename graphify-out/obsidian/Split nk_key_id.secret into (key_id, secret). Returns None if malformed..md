---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L42"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Split "nk_<key_id>.<secret>" into (key_id, secret). Returns None if malformed.

## Connections
- [[parse_token()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware