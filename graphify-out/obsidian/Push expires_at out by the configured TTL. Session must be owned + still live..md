---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "rationale"
community: "Auth & Error Handling"
location: "L202"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Auth_&_Error_Handling
---

# Push expires_at out by the configured TTL. Session must be owned + still live.

## Connections
- [[extend_my_session()]] - `rationale_for` [EXTRACTED]
- [[verify_totp()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Auth_&_Error_Handling