---
source_file: "backend/01_core/response.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# core response (success/error/paginated envelope helpers)

## Connections
- [[Response envelope pattern ({ok, data}  {ok, error {code, message}})]] - `implements` [EXTRACTED]
- [[audit.saved_views routes]] - `calls` [EXTRACTED]
- [[backend.01_core.middleware (Bearer token validation)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature