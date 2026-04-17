---
source_file: "backend/02_features/02_vault/crypto.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# vault crypto (AES-256-GCM envelope encrypt/decrypt)

## Connections
- [[ADR-028 vault envelope encryption rationale]] - `rationale_for` [EXTRACTED]
- [[Envelope dataclass (ciphertext, wrapped_dek, nonce)]] - `implements` [EXTRACTED]
- [[vault bootstrap (ensure_bootstrap_secrets)]] - `conceptually_related_to` [INFERRED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization