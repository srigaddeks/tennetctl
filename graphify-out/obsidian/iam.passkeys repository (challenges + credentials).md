---
source_file: "backend/02_features/03_iam/sub_features/13_passkeys/repository.py"
type: "code"
community: "WebAuthn Passkeys"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/WebAuthn_Passkeys
---

# iam.passkeys repository (challenges + credentials)

## Connections
- [[DB table 03_iam.25_fct_iam_passkey_challenges]] - `references` [EXTRACTED]
- [[DB table 03_iam.26_fct_iam_passkey_credentials]] - `references` [EXTRACTED]
- [[iam.passkeys routes (v1authpasskeys)]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/WebAuthn_Passkeys