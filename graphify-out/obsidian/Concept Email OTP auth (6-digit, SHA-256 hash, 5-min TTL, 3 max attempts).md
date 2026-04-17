---
source_file: "backend/02_features/03_iam/sub_features/12_otp/service.py"
type: "document"
community: "Error Types & Authorization"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# Concept: Email OTP auth (6-digit, SHA-256 hash, 5-min TTL, 3 max attempts)

## Connections
- [[iam.otp service layer (email OTP + TOTP)]] - `implements` [EXTRACTED]
- [[notify.send.transactional — node key for programmatic sends]] - `conceptually_related_to` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Error_Types_&_Authorization