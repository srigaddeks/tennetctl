---
source_file: "backend/02_features/02_vault/bootstrap.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# vault bootstrap (ensure_bootstrap_secrets)

## Connections
- [[vault crypto (AES-256-GCM envelope encryptdecrypt)]] - `conceptually_related_to` [INFERRED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `conceptually_related_to` [INFERRED]
- [[vault.secrets repository (get_metadata_by_scope_key used by bootstrap)]] - `calls` [EXTRACTED]
- [[vault.secrets service (create_secret used by bootstrap)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization