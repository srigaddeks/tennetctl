---
source_file: "backend/02_features/03_iam/sub_features/13_passkeys/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.passkeys service — WebAuthn FIDO2 registration + authentication

## Connections
- [[Concept WebAuthn two-phase ceremony (begin challenge → complete verification)]] - `implements` [EXTRACTED]
- [[IAM feature router — aggregates all sub-feature routers]] - `references` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `shares_data_with` [INFERRED]
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - `calls` [EXTRACTED]
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - `calls` [EXTRACTED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization