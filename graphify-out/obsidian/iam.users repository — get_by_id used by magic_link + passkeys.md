---
source_file: "backend/02_features/03_iam/sub_features/03_users/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.users repository — get_by_id used by magic_link + passkeys

## Connections
- [[Concept User EAV attributes (email, display_name, avatar_url in dtl_attrs)]] - `implements` [EXTRACTED]
- [[DB table 03_iam.02_dim_account_types]] - `references` [EXTRACTED]
- [[DB table 03_iam.12_fct_users]] - `references` [EXTRACTED]
- [[DB table 03_iam.21_dtl_attrs (EAV user attributes)]] - `references` [EXTRACTED]
- [[DB view 03_iam.v_users]] - `references` [EXTRACTED]
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `calls` [EXTRACTED]
- [[iam.otp service layer (email OTP + TOTP)]] - `calls` [EXTRACTED]
- [[iam.passkeys service — WebAuthn FIDO2 registration + authentication]] - `calls` [EXTRACTED]
- [[iam.users service layer]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization