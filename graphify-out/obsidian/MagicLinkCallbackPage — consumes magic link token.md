---
source_file: "frontend/src/app/auth/magic-link/callback/page.tsx"
type: "code"
community: "API Endpoint Type Catalog"
location: "line 66"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Endpoint_Type_Catalog
---

# MagicLinkCallbackPage — consumes magic link token

## Connections
- [[AuthResponseBody — token + user + session]] - `shares_data_with` [EXTRACTED]
- [[POST v1authmagic-linkconsume — magic link token exchange]] - `calls` [EXTRACTED]
- [[apiFetch  apiList — typed HTTP client with ok-envelope check]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Endpoint_Type_Catalog