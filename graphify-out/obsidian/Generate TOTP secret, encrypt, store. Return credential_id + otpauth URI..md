---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L168"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Generate TOTP secret, encrypt, store. Return credential_id + otpauth URI.

## Connections
- [[setup_totp()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer