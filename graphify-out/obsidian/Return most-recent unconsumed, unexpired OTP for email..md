---
source_file: "backend/02_features/03_iam/sub_features/12_otp/repository.py"
type: "rationale"
community: "Auth & Error Handling"
location: "L34"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Auth_&_Error_Handling
---

# Return most-recent unconsumed, unexpired OTP for email.

## Connections
- [[get_active_otp()]] - `rationale_for` [EXTRACTED]
- [[get_by_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Auth_&_Error_Handling