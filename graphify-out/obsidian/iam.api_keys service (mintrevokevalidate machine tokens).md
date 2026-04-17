---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/service.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.api_keys service (mint/revoke/validate machine tokens)

## Connections
- [[API key token format nk_key_id.secret (argon2id-hashed)]] - `implements` [EXTRACTED]
- [[Concept API key Bearer authentication (nk_ prefix, argon2id, session-only mint)]] - `implements` [EXTRACTED]
- [[Node audit.events.emit (audit event sink)]] - `calls` [EXTRACTED]
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[backend.01_core.middleware (Bearer token validation)]] - `calls` [EXTRACTED]
- [[iam.api_keys repository (v_iam_api_keys view + fct)]] - `calls` [EXTRACTED]
- [[iam.api_keys routes (v1api-keys)]] - `calls` [EXTRACTED]
- [[iam.credentials service (argon2id hashverify helper)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature