---
source_file: "backend/02_features/03_iam/sub_features/11_magic_link/routes.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.magic_link routes — /v1/auth/magic-link/request + /consume

## Connections
- [[IAM feature router — aggregates all sub-feature routers]] - `references` [EXTRACTED]
- [[iam.magic_link schemas — MagicLinkRequestConsumeRequestResponse]] - `references` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `calls` [EXTRACTED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization