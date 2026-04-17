---
source_file: "backend/01_core/middleware.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# backend.01_core.middleware (Bearer token validation)

## Connections
- [[IAM API keys service (validate_token)]] - `calls` [EXTRACTED]
- [[SessionMiddleware dual-auth API key (nk_ prefix) + session token]] - `implements` [EXTRACTED]
- [[core errors (AppError hierarchy NotFound, Validation, Conflict, Forbidden, Unauthorized)]] - `shares_data_with` [EXTRACTED]
- [[core id (uuid7 generator)]] - `calls` [EXTRACTED]
- [[core response (successerrorpaginated envelope helpers)]] - `calls` [EXTRACTED]
- [[iam.api_keys service (mintrevokevalidate machine tokens)]] - `calls` [EXTRACTED]
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature