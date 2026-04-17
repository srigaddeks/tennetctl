---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L86"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Service_&_Repository_Layer
---

# mint_session()

## Connections
- [[Create a session row and return (token, session_metadata).]] - `rationale_for` [EXTRACTED]
- [[_resolve_ttl_days()]] - `calls` [EXTRACTED]
- [[_signing_key_bytes()]] - `calls` [EXTRACTED]
- [[auth_complete()]] - `calls` [INFERRED]
- [[consume_magic_link()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[insert_session()]] - `calls` [INFERRED]
- [[make_token()]] - `calls` [EXTRACTED]
- [[oauth_signin()]] - `calls` [INFERRED]
- [[service.py_23]] - `contains` [EXTRACTED]
- [[signin()]] - `calls` [INFERRED]
- [[signup()]] - `calls` [INFERRED]
- [[uuid7()]] - `calls` [INFERRED]
- [[verify_otp()]] - `calls` [INFERRED]
- [[verify_totp()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Service_&_Repository_Layer