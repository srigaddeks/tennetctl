---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L49"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# _signing_key_bytes()

## Connections
- [[.invalidate()]] - `calls` [INFERRED]
- [[Fetch + base64-decode the signing key. Cached upstream by VaultClient (60s).]] - `rationale_for` [EXTRACTED]
- [[NodeContext]] - `calls` [INFERRED]
- [[Resolve email address for a delivery recipient.     Looks up 03_iam.v_users]] - `rationale_for` [EXTRACTED]
- [[_apply_unsubscribe()]] - `calls` [INFERRED]
- [[_send_one()]] - `calls` [INFERRED]
- [[consume_magic_link()]] - `calls` [EXTRACTED]
- [[get()_1]] - `calls` [INFERRED]
- [[mint_session()]] - `calls` [EXTRACTED]
- [[request_magic_link()]] - `calls` [EXTRACTED]
- [[service.py_1]] - `contains` [EXTRACTED]
- [[service.py_12]] - `contains` [EXTRACTED]
- [[service.py_23]] - `contains` [EXTRACTED]
- [[uuid7()]] - `calls` [INFERRED]
- [[validate_token()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Session_Auth_&_Middleware