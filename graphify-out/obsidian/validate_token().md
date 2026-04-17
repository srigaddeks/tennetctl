---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L116"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# validate_token()

## Connections
- [[.dispatch()_2]] - `calls` [INFERRED]
- [[.run()_20]] - `calls` [INFERRED]
- [[Look up + verify a Bearer token. Returns the key row on success, else None.]] - `rationale_for` [EXTRACTED]
- [[Return the session row iff signature matches AND row is_valid. Else None.]] - `rationale_for` [EXTRACTED]
- [[_signing_key_bytes()]] - `calls` [EXTRACTED]
- [[get()_1]] - `calls` [INFERRED]
- [[get_active_by_key_id()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[parse_token()]] - `calls` [EXTRACTED]
- [[service.py_14]] - `contains` [EXTRACTED]
- [[service.py_23]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Session_Auth_&_Middleware