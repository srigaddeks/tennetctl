---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L50"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Fetch + base64-decode the signing key. Cached upstream by VaultClient (60s).

## Connections
- [[_signing_key_bytes()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware