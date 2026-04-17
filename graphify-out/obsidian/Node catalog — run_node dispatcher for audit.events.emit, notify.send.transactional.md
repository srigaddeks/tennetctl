---
source_file: "backend/01_catalog/__init__.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional

## Connections
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - `calls` [EXTRACTED]
- [[iam.memberships service layer]] - `calls` [EXTRACTED]
- [[iam.otp service layer (email OTP + TOTP)]] - `calls` [EXTRACTED]
- [[iam.roles service — CRUD with EAV attributes]] - `calls` [EXTRACTED]
- [[iam.users service layer]] - `calls` [EXTRACTED]
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization