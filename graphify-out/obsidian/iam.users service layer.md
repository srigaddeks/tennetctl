---
source_file: "backend/02_features/03_iam/sub_features/03_users/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.users service layer

## Connections
- [[Concept User EAV attributes (email, display_name, avatar_url in dtl_attrs)]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[Node audit.events.emit]] - `calls` [EXTRACTED]
- [[Node iam.users.create (effect)]] - `calls` [EXTRACTED]
- [[Node iam.users.get (control)]] - `calls` [EXTRACTED]
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - `calls` [EXTRACTED]
- [[iam.users FastAPI routes]] - `calls` [EXTRACTED]
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization