---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "rationale"
community: "Core Infrastructure"
location: "L49"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Core_Infrastructure
---

# Envelope-encrypt TOTP secret using vault root key. Returns (ciphertext_b64, dek_

## Connections
- [[_encrypt_secret()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Core_Infrastructure