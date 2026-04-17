---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "document"
community: "Error Types & Authorization"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# Concept: TOTP secret envelope-encrypted via vault root key (DEK + nonce)

## Connections
- [[Concept TOTP auth (RFC 6238, pyotp, 30s window, vault-encrypted secret)]] - `conceptually_related_to` [EXTRACTED]
- [[backend.02_features.02_vault.crypto (Envelope encryptdecrypt)]] - `rationale_for` [EXTRACTED]
- [[iam.otp service layer (email OTP + TOTP)]] - `implements` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Error_Types_&_Authorization