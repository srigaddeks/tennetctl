---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/repository.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L93"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Push expires_at to `new_expires_at` iff the session is still live + unrevoked.

## Connections
- [[extend_expires()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware