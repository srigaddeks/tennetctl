# K-Protect — Overview

## What is k-protect?

K-Protect is the real-time policy engine for behavioral fraud prevention. It sits between the kbio behavioral intelligence layer and the calling application, evaluating ordered policy sets against live session signals to produce enforcement decisions (allow, challenge, block, monitor, flag, throttle).

It is a **client application** registered in tennetctl. All authentication, identity management, RBAC, and feature flags are delegated to tennetctl — k-protect itself contains no auth infrastructure. Policy rules are scoped by `org_id` and `workspace_id` from the tennetctl IAM context.

## Architecture

```
Client SDK / Application
        |
        | POST /v1/evaluate
        |   Authorization: Bearer <kprotect_api_key>
        |   { "session_id": "...", "policy_set_id": "..." }
        |
        v
k-protect backend (FastAPI, port 8200)
        |
        |--- GET kbio scores ----> k-forensics backend (port 8100)
        |                               |
        |                               v
        |                          kbio schema (10_kbio)
        |                          behavioral scores, session state
        |
        |--- evaluate policies --> 11_kprotect schema (PostgreSQL)
        |                          policy selections, policy sets, decisions
        |
        v
Decision response
  { "ok": true, "data": { "outcome": "blocked", "action": "block", ... } }
```

The evaluate flow:
1. Client presents API key (`12_fct_api_keys` — key_hash verified)
2. kprotect fetches the active policy set for the org (or uses the `policy_set_id` parameter)
3. For each policy selection in the set (ordered by sort_order), kprotect fetches the kbio behavioral score for the session
4. Each predefined policy's conditions are evaluated against the score signals
5. The aggregate outcome is resolved (short-circuit or evaluate-all mode)
6. The decision is logged to `60_evt_decisions` + `61_evt_decision_details`
7. The enforcement action is returned to the caller

## IAM Integration

K-Protect is registered in tennetctl as a separate application (`k-protect`). It shares the same org as all other tennetctl applications — no duplicate orgs are created.

When a user signs in to the k-protect dashboard, the frontend calls:

```
POST /v1/applications/k-protect/resolve-access
Authorization: Bearer <user_jwt>
X-Application-Token: <app_token>
Content-Type: application/json

{ "environment": "dev" }
```

tennetctl validates both tokens and returns a single JSON blob containing:
- The user's org-tier roles (`k_protect.admin`, `k_protect.analyst`, `k_protect.viewer`)
- Group memberships (`k_protect_admins`, `k_protect_analysts`)
- Effective permissions (union of all role grants)
- Evaluated feature flags for the environment
- Linked products (`kprotect-engine`, `kprotect-dashboard`)

K-Protect uses this payload to gate dashboard UI features, routes, and actions.

## Ports

| Service | Port |
| --- | --- |
| tennetctl backend | 58000 |
| k-forensics backend (kbio) | 8100 |
| k-protect backend | 8200 |
| k-protect frontend (future) | 3200 |

## Database Schema

Schema: `11_kprotect` (within the shared tennetctl PostgreSQL database).

| Table | Type | Purpose |
| --- | --- | --- |
| `10_fct_policy_selections` | fct | Org's selection of a predefined kbio policy |
| `11_fct_policy_sets` | fct | Named collection of policy selections |
| `12_fct_api_keys` | fct | API key credentials for the evaluate endpoint |
| `20_dtl_attrs` | dtl | EAV attributes for all three entity types |
| `40_lnk_policy_set_selections` | lnk | M2M link: policy set → policy selections |
| `60_evt_decisions` | evt | Per-evaluate-call decision log |
| `61_evt_decision_details` | evt | Per-policy breakdown of each decision |

## Roles and Permissions

| Role | Description |
| --- | --- |
| `k_protect.admin` | Full access: manage policies, sets, API keys, install library policies |
| `k_protect.analyst` | Read + test policies, view decisions. No create/modify. |
| `k_protect.viewer` | Read-only: policies, policy sets, decisions |

## Dev Setup

```bash
# 1. Start tennetctl first (required)
cd /path/to/tennetctl && ./dev.sh

# 2. Start k-protect backend
cd 10_apps/02_k-protect && ./dev.sh
```

Backend runs at `http://localhost:8200`. All IAM/auth endpoints are proxied transparently to tennetctl.

See `03_docs/01_seeding.md` for first-time seeding instructions.

## Folder Structure

```
10_apps/02_k-protect/
├── 03_docs/
│   ├── 00_overview.md          — this file
│   ├── 01_seeding.md           — seeding instructions
│   ├── 02_features/            — per-feature migrations
│   │   └── 11_kprotect/
│   │       └── 05_sub_features/
│   │           └── 00_bootstrap/
│   │               └── 09_sql_migrations/02_in_progress/
│   └── 03_seed/                — seed data JSON + SQL
│       ├── 00_permissions.sql
│       ├── 01_application.json
│       ├── 02_products.json
│       ├── 05_roles.json
│       ├── 06_groups.json
│       ├── 07_role_permissions.json
│       └── 08_application_products.json
├── 04_backend/
│   ├── pyproject.toml
│   ├── 01_core/                — config, db, valkey, errors, response, app
│   └── 02_proxy/               — reverse proxy middleware to tennetctl
└── dev.sh                      — dev launcher
```

## Dependencies

- tennetctl must be running at `http://localhost:58000`
- k-forensics (kbio) must be running at `http://localhost:8100` for score fetching
- DB must have been migrated through migrations 025–027 (`11_kprotect` schema)
