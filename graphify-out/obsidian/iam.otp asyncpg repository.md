---
source_file: "backend/02_features/03_iam/sub_features/12_otp/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.otp asyncpg repository

## Connections
- [[DB table 03_iam.23_fct_iam_otp_codes]] - `references` [EXTRACTED]
- [[DB table 03_iam.24_fct_iam_totp_credentials]] - `references` [EXTRACTED]
- [[iam.otp service layer (email OTP + TOTP)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization