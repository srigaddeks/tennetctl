---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L161"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Service_&_Repository_Layer
---

# setup_totp()

## Connections
- [[Generate TOTP secret, encrypt, store. Return credential_id + otpauth URI.]] - `rationale_for` [EXTRACTED]
- [[_encrypt_secret()]] - `calls` [EXTRACTED]
- [[create_totp_credential()]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[service.py_20]] - `contains` [EXTRACTED]
- [[setup_totp_route()]] - `calls` [INFERRED]
- [[uuid7()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Service_&_Repository_Layer