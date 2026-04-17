---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "code"
community: "Auth & Error Handling"
location: "L195"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Auth_&_Error_Handling
---

# verify_totp()

## Connections
- [[AppError]] - `calls` [INFERRED]
- [[Push expires_at out by the configured TTL. Session must be owned + still live.]] - `rationale_for` [EXTRACTED]
- [[_decrypt_secret()]] - `calls` [EXTRACTED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[get_totp_credential()]] - `calls` [INFERRED]
- [[mark_totp_used()]] - `calls` [INFERRED]
- [[mint_session()]] - `calls` [INFERRED]
- [[service.py_20]] - `contains` [EXTRACTED]
- [[verify_totp_route()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Auth_&_Error_Handling