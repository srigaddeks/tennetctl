---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# iam.auth service layer (signup/signin/signout/OAuth)

## Connections
- [[Concept OAuth signin (Google + GitHub code exchange, user upsert)]] - `implements` [EXTRACTED]
- [[Concept Single-tenant default org auto-attach on signupsignin]] - `implements` [EXTRACTED]
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - `calls` [EXTRACTED]
- [[Node audit.events.emit]] - `calls` [EXTRACTED]
- [[iam.memberships asyncpg repository]] - `calls` [EXTRACTED]
- [[iam.memberships service layer]] - `calls` [EXTRACTED]
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - `calls` [EXTRACTED]
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - `calls` [EXTRACTED]
- [[iam.users service layer]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization