---
source_file: "backend/02_features/03_iam/sub_features/13_passkeys/routes.py"
type: "code"
community: "WebAuthn Passkeys"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/WebAuthn_Passkeys
---

# iam.passkeys routes (/v1/auth/passkeys)

## Connections
- [[Concept WebAuthn passkey registerauth flow (challenge-response, sign_count replay protection)]] - `implements` [EXTRACTED]
- [[DB table 03_iam.25_fct_iam_passkey_challenges]] - `references` [INFERRED]
- [[DB table 03_iam.26_fct_iam_passkey_credentials]] - `references` [INFERRED]
- [[iam.passkeys repository (challenges + credentials)]] - `calls` [INFERRED]
- [[iam.passkeys schemas (WebAuthn)]] - `references` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/WebAuthn_Passkeys