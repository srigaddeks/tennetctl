---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L73"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# parse_token()

## Connections
- [[Split nk_key_id.secret into (key_id, secret). Returns None if malformed.]] - `rationale_for` [EXTRACTED]
- [[Validate signature + return embedded session_id, or None if tampered.]] - `rationale_for` [EXTRACTED]
- [[_sign()]] - `calls` [EXTRACTED]
- [[service.py_14]] - `contains` [EXTRACTED]
- [[service.py_23]] - `contains` [EXTRACTED]
- [[validate_token()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Session_Auth_&_Middleware