---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "rationale"
community: "Auth & Error Handling"
location: "L135"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Auth_&_Error_Handling
---

# Verify OTP code; return (session_token, user, session) on success.

## Connections
- [[is_opted_in()]] - `rationale_for` [EXTRACTED]
- [[verify_otp()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Auth_&_Error_Handling