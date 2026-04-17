---
source_file: "backend/02_features/03_iam/sub_features/05_groups/service.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# iam.groups service (CRUD: create, get, list, update, delete with audit emission)

## Connections
- [[Groups as RBAC building block org-scoped, code-unique per org, EAV attributes (codelabeldescription)]] - `implements` [EXTRACTED]
- [[Node iam.groups.create (effect node — create group via service)]] - `calls` [EXTRACTED]
- [[Node iam.groups.get (control node — fetch group by id)]] - `calls` [EXTRACTED]
- [[iam.groups FastAPI routes (GET list, POST create, GET one, PATCH update, DELETE soft-delete)]] - `calls` [EXTRACTED]
- [[iam.groups repository (asyncpg, entity_type_id=5, v_groups view, 14_fct_groups, EAV attrs)]] - `calls` [EXTRACTED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes