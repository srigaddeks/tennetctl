# SolSocial

A lightweight Buffer-alternative built on top of TennetCTL.

Only business logic lives here. Auth, RBAC scopes, users/orgs/workspaces, audit,
notifications, vault (OAuth token storage), and feature flags are proxied to
tennetctl. SolSocial owns only: social channels, posts, queues, ideas, and its
own app-level RBAC (solsocial-specific roles/permissions and feature toggles).

## Layout

```
apps/solsocial/
├── 03_docs/features/10_solsocial/
│   ├── feature.manifest.yaml
│   └── 05_sub_features/
│       ├── 00_bootstrap/09_sql_migrations/
│       │   ├── 02_in_progress/   # new migrations land here
│       │   ├── 01_migrated/      # runner moves files here after apply
│       │   └── seeds/            # YAML seeds for dim_* tables
│       ├── 10_channels/09_sql_migrations/
│       ├── 20_posts/09_sql_migrations/
│       ├── 30_queues/09_sql_migrations/
│       ├── 50_ideas/09_sql_migrations/
│       ├── 70_rbac/09_sql_migrations/
│       └── 80_feature_registry/09_sql_migrations/
├── backend/
│   ├── main.py
│   ├── 01_core/              # config, db, id, response, errors, middleware,
│   │                         # tennetctl_client, authz
│   ├── 02_features/
│   │   ├── 10_channels/      # 5-file sub-feature (schemas/repo/service/routes)
│   │   ├── 20_posts/
│   │   ├── 30_queue/
│   │   ├── 40_calendar/      # read-only aggregate (routes only)
│   │   ├── 50_ideas/
│   │   └── 60_oauth/         # provider adapters + OAuth flow routes
│   ├── scripts/
│   │   └── migrator.py       # thin wrapper → tennetctl's runner
│   └── tests/                # pytest smoke tests
└── frontend/                 # Next.js — composer, queue, calendar, ideas
```

## Proxied to tennetctl (NEVER duplicated here)

| Concern                       | How                                                                        | Auth used            |
|-------------------------------|----------------------------------------------------------------------------|----------------------|
| End-user identity             | `GET /v1/auth/me` — user's session bearer forwarded                        | user session token   |
| Audit emission                | `POST /v1/audit-events` — user context goes in metadata                    | service API key      |
| Notifications                 | `POST /v1/notify/send`                                                     | service API key      |
| OAuth tokens (secret)         | `POST /v1/vault` — `vault_key` saved on channel                            | service API key      |
| Feature flags (evaluate/list) | `POST /v1/feature-flags/evaluate` + `GET /v1/feature-flags?application_id=`| service API key      |
| Roles / applications          | `GET /v1/roles?application_id=…`, `GET /v1/applications`                   | service API key      |

Only `whoami` uses the user's session token — API keys don't carry a
`session_id`, and `/v1/auth/me` requires session auth. Everything else is
server-to-server and uses the solsocial **service API key**.

## Minting the service API key

1. Sign in to tennetctl as an admin user and grab your session bearer.
2. Mint a key via tennetctl's `/v1/api-keys` endpoint:

   ```bash
   curl -X POST http://localhost:51734/v1/api-keys \
     -H "Authorization: Bearer $SESSION_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "label": "solsocial-service",
       "scopes": [
         "iam:applications:read",
         "iam:roles:read",
         "iam:roles:write",
         "flags:view:org",
         "flags:write:org",
         "notify:send",
         "audit:write",
         "vault:read:org",
         "vault:write:org"
       ]
     }'
   ```

   The response includes a one-time `token` field (`nk_<key_id>.<secret>`).
   That value is never shown again.

3. Save the token into a file and point solsocial at it:

   ```bash
   mkdir -p apps/solsocial/backend/secrets
   echo "nk_…" > apps/solsocial/backend/secrets/tennetctl.key
   chmod 600 apps/solsocial/backend/secrets/tennetctl.key
   export SOLSOCIAL_TENNETCTL_KEY_FILE=./apps/solsocial/backend/secrets/tennetctl.key
   ```

4. Run the bootstrap — it registers the solsocial application + roles + flags:

   ```bash
   .venv/bin/python -m apps.solsocial.backend.scripts.bootstrap_tennetctl \
     --org-id <tennetctl-org-uuid>
   ```

   First-time bootstrap only: if the API key lacks `iam:applications:write`
   you can pass `--session-token <token>` instead of using the key.

SolSocial-local RBAC (who can publish vs draft only) lives in the solsocial DB
because it must be enforced atomically with business transactions.

## Databases

Two separate Postgres databases on the same server:

- `tennetctl` — tennetctl platform DB (unchanged)
- `solsocial` — solsocial business DB (this app)

Both databases track migrations in their own `"00_schema_migrations"` schema
via the same migrator runner.

## Ports

| Service             | Port  |
|---------------------|-------|
| tennetctl backend   | 51734 |
| tennetctl frontend  | 51735 |
| solsocial backend   | 51834 |
| solsocial frontend  | 51835 |

## Migrations — same convention as tennetctl

Migrations live inside their sub-feature directories and are applied in global
filename order (`YYYYMMDD_NNN_*.sql`). Each file has `-- UP ====` and
`-- DOWN ====` sections. Seeds are YAML (or JSON) and idempotent.

```bash
# Create the solsocial DB (if missing) and apply pending migrations
.venv/bin/python -m apps.solsocial.backend.scripts.migrator apply

# Populate dim_* tables + the role→permission matrix
.venv/bin/python -m apps.solsocial.backend.scripts.migrator seed

# See what's pending / applied
.venv/bin/python -m apps.solsocial.backend.scripts.migrator status

# Scaffold a new migration in the right sub-feature dir
.venv/bin/python -m apps.solsocial.backend.scripts.migrator new \
    --name add-post-reactions --feature 10_solsocial --sub 20_posts

# Roll back the last applied migration (or `--to <filename>`)
.venv/bin/python -m apps.solsocial.backend.scripts.migrator rollback
```

The wrapper just forwards to `backend.01_migrator.runner` with
`--root apps/solsocial` and `--dsn <solsocial-url>` — identical verbs, file
format, and behaviour to tennetctl's migrator.

## Run

```bash
# 1. Bring up shared infra
docker-compose up -d

# 2. Start tennetctl backend (provides /v1/auth/me, /v1/notify, /v1/vault, ...)
.venv/bin/python -m uvicorn backend.main:app --port 51734 --reload

# 3. Apply solsocial migrations + seeds
.venv/bin/python -m apps.solsocial.backend.scripts.migrator apply
.venv/bin/python -m apps.solsocial.backend.scripts.migrator seed

# 4. Start solsocial backend
.venv/bin/python -m uvicorn apps.solsocial.backend.main:app --port 51834 --reload

# 5. Start solsocial frontend
cd apps/solsocial/frontend && npm install && npm run dev
```

## Publisher modes

`SOLSOCIAL_PUBLISHER_MODE=stub` (default) uses synthetic adapters — OAuth
returns a fake handle, publishes return a synthetic `external_post_id`. This
lets the full pipeline be exercised without real LinkedIn/Twitter/Instagram
credentials.

`SOLSOCIAL_PUBLISHER_MODE=live` requires provider secrets in the tennetctl
vault under `solsocial.oauth.{provider}.client_id|client_secret`.
