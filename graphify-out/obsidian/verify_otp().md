---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "code"
community: "Auth & Error Handling"
location: "L128"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Auth_&_Error_Handling
---

# verify_otp()

## Connections
- [[AppError]] - `calls` [INFERRED]
- [[Verify OTP code; return (session_token, user, session) on success.]] - `rationale_for` [EXTRACTED]
- [[_hash_code()]] - `calls` [EXTRACTED]
- [[get_active_otp()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[increment_otp_attempts()]] - `calls` [INFERRED]
- [[mark_otp_consumed()]] - `calls` [INFERRED]
- [[mint_session()]] - `calls` [INFERRED]
- [[service.py_20]] - `contains` [EXTRACTED]
- [[verify_otp_route()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Auth_&_Error_Handling