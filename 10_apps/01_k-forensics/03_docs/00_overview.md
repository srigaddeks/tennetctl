# K-Forensics — Overview

## What is k-forensics?

K-Forensics is a digital forensics and case management SaaS platform for security teams. It enables investigators to create and manage cases, track evidence, and produce investigation reports.

It is a **client application** registered in tennetctl. All authentication, identity management, RBAC, and feature flags are delegated to tennetctl — k-forensics itself contains no auth infrastructure.

## Architecture

```
k-forensics frontend (Next.js, port 3100)
        |
        | POST /v1/applications/k-forensics/resolve-access
        |   Authorization: Bearer <user_jwt>
        |   X-Application-Token: <app_token>
        |
        v
tennetctl API (FastAPI, port 58000)
  - Auth / Sessions   → /v1/sessions
  - IAM / Orgs        → /v1/orgs
  - RBAC Roles        → /v1/orgs/{org_id}/roles
  - Groups            → /v1/groups
  - Products          → /v1/products
  - Feature Flags     → /v1/feature-flags
  - Applications      → /v1/applications
        |
        v
PostgreSQL (tennetctl DB)
```

### resolve-access flow

When a user signs in to k-forensics, the frontend calls:

```
POST /v1/applications/k-forensics/resolve-access
Authorization: Bearer <user_jwt>
X-Application-Token: <app_token>
Content-Type: application/json

{ "environment": "dev" }
```

tennetctl validates both tokens, then returns a single JSON blob containing:
- The user's org-tier roles
- Group memberships
- Effective permissions (union of all role grants)
- Evaluated feature flags for the environment
- Linked products

k-forensics uses this payload to gate UI features, routes, and actions. No RBAC logic lives inside k-forensics.

## Dev setup

### Start the app

```bash
cd 10_apps/01_k-forensics/06_frontend
npm run dev
# App runs at http://localhost:3100
```

### Required env vars

Create `06_frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:58000
NEXT_PUBLIC_APPLICATION_CODE=k-forensics
NEXT_PUBLIC_APPLICATION_TOKEN=<paste token from tennetctl UI>
```

The application token is obtained from the tennetctl UI after seeding:
IAM → Applications → k-forensics → Tokens tab → Issue Token → copy the raw token (shown once only).

## Folder structure

```
10_apps/01_k-forensics/
├── 03_docs/
│   ├── 00_overview.md          ← this file
│   ├── 01_seeding.md           ← seeding instructions
│   ├── 02_features/            ← per-feature docs (gitkeep for now)
│   ├── 03_seed/                ← seed data JSON + SQL
│   │   ├── 00_permissions.sql
│   │   ├── 01_application.json
│   │   ├── 02_products.json
│   │   ├── 05_roles.json
│   │   ├── 06_groups.json
│   │   ├── 07_role_permissions.json
│   │   └── 08_application_products.json
│   └── 04_seed.py              ← idempotent seeder script
├── 04_backend/                 ← k-forensics backend (if any)
└── 06_frontend/                ← Next.js app (port 3100)
    ├── src/app/
    │   ├── sign-in/
    │   ├── sign-up/
    │   ├── orgs/
    │   ├── settings/
    │   └── workspace/
    └── .env.local              ← NEXT_PUBLIC_* vars (git-ignored)
```

## Dependencies

tennetctl must be running at `http://localhost:58000` and the DB must have been migrated through at least migration `013_iam_applications.sql` before k-forensics can operate.

See `03_docs/01_seeding.md` for first-time setup.
