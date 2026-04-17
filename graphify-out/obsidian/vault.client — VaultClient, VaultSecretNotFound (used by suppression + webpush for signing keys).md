---
source_file: "backend/02_features/02_vault/client.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)

## Connections
- [[DB table 02_vault.10_fct_vault_entries (encrypted secrets rows)]] - `references` [EXTRACTED]
- [[Envelope dataclass (ciphertext, wrapped_dek, nonce)]] - `references` [EXTRACTED]
- [[iam.magic_link routes — v1authmagic-linkrequest + consume]] - `references` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `calls` [EXTRACTED]
- [[iam.passkeys service — WebAuthn FIDO2 registration + authentication]] - `calls` [EXTRACTED]
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `calls` [EXTRACTED]
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - `calls` [EXTRACTED]
- [[vault bootstrap (ensure_bootstrap_secrets)]] - `conceptually_related_to` [INFERRED]
- [[vault crypto (AES-256-GCM envelope encryptdecrypt)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization