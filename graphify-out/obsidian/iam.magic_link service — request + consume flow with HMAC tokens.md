---
source_file: "backend/02_features/03_iam/sub_features/11_magic_link/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.magic_link service — request + consume flow with HMAC tokens

## Connections
- [[Concept HMAC-SHA256 signed tokens for magic-link security (no raw token stored)]] - `implements` [EXTRACTED]
- [[Concept no user enumeration — magic_link returns 'sent' regardless of user existence]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[iam.magic_link repository — 19_fct_iam_magic_link_tokens]] - `calls` [EXTRACTED]
- [[iam.magic_link routes — v1authmagic-linkrequest + consume]] - `calls` [EXTRACTED]
- [[iam.passkeys service — WebAuthn FIDO2 registration + authentication]] - `shares_data_with` [INFERRED]
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - `conceptually_related_to` [INFERRED]
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - `calls` [EXTRACTED]
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - `conceptually_related_to` [INFERRED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization