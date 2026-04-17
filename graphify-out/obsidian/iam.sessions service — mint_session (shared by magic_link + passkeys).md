---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.sessions service — mint_session (shared by magic_link + passkeys)

## Connections
- [[backend.01_core.middleware (Bearer token validation)]] - `calls` [EXTRACTED]
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `conceptually_related_to` [INFERRED]
- [[iam.otp service layer (email OTP + TOTP)]] - `calls` [EXTRACTED]
- [[iam.passkeys service — WebAuthn FIDO2 registration + authentication]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization