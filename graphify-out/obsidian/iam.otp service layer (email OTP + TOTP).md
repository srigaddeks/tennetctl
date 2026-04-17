---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.otp service layer (email OTP + TOTP)

## Connections
- [[Concept Email OTP auth (6-digit, SHA-256 hash, 5-min TTL, 3 max attempts)]] - `implements` [EXTRACTED]
- [[Concept TOTP auth (RFC 6238, pyotp, 30s window, vault-encrypted secret)]] - `implements` [EXTRACTED]
- [[Concept TOTP secret envelope-encrypted via vault root key (DEK + nonce)]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[backend.02_features.02_vault.crypto (Envelope encryptdecrypt)]] - `calls` [EXTRACTED]
- [[iam.otp FastAPI routes (v1authotp, v1authtotp)]] - `calls` [EXTRACTED]
- [[iam.otp asyncpg repository]] - `calls` [EXTRACTED]
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - `calls` [EXTRACTED]
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - `calls` [EXTRACTED]
- [[notify.send.transactional — node key for programmatic sends]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization