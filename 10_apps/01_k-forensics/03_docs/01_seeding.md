# K-Forensics — Seeding Instructions

Run these steps once after a fresh tennetctl install, or any time after wiping the database.
The seeder is fully idempotent — every step is safe to re-run.

## Prerequisites

- tennetctl is running: `http://localhost:58000`
- DB has been migrated (includes `013_iam_applications.sql` or later)
- Admin credentials from the tennetctl setup wizard

## Step 1 — Boot tennetctl and run migrations

```bash
# Start tennetctl (from the tennetctl repo root)
.venv/bin/python -m uvicorn 04_backend.main:app --port 58000 --host 0.0.0.0 --reload

# In a second terminal, run the SQL migrator (picks up any pending migrations)
.venv/bin/python -m scripts.migrator
```

Confirm that `013_iam_applications.sql` (or later) appears in the migrated list.

## Step 2 — Run the seeder

```bash
cd 10_apps/01_k-forensics

python 03_docs/04_seed.py \
  --api-url http://localhost:58000 \
  --admin-username admin \
  --admin-password ChangeMe123!
```

Optional flag: `--org-code <code>` to target a specific org (defaults to the first org returned).

The seeder creates, in order:
1. The `k-forensics` application (category: `saas_web`)
2. The `kbio` product (category: `saas_app`)
3. K-forensics-specific permissions (`cases`, `evidence`, `reports`)
4. Three org-tier roles: `k_forensics.admin`, `k_forensics.investigator`, `k_forensics.viewer`
5. Two default groups: `k_forensics_admins`, `k_forensics_investigators`
6. Role-permission grants for all three roles
7. Links the `kbio` product to the `k-forensics` application

All operations are idempotent. A 409 Conflict response is treated as success ("already exists, skipping").

### Permissions fallback

If the permissions API endpoint is not yet available (returns 404/405), the seeder will print:

```
WARNING: Permissions API not available. Run manually:
  psql $DATABASE_URL -f 03_seed/00_permissions.sql
```

In that case, run the SQL fallback before re-running the seeder.

## Step 3 — Issue an application token

The seeder does NOT issue application tokens — the raw token must stay in the operator's hands only.

1. Open tennetctl UI: `http://localhost:48000` (or wherever the UI runs)
2. Navigate to: IAM → Applications → k-forensics → Tokens tab
3. Click "Issue Token"
4. Copy the raw token (displayed once only — it is hashed immediately after)

## Step 4 — Configure the frontend

Create `06_frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:58000
NEXT_PUBLIC_APPLICATION_CODE=k-forensics
NEXT_PUBLIC_APPLICATION_TOKEN=<paste the token from Step 3>
```

## Step 5 — Start k-forensics

```bash
cd 10_apps/01_k-forensics/06_frontend
npm run dev
# App available at http://localhost:3100
```

## Step 6 — Sign in

1. Open `http://localhost:3100`
2. Sign in with any user account (created via the tennetctl UI or API)
3. On successful login, k-forensics calls `POST /v1/applications/k-forensics/resolve-access` with both the user JWT and the application token
4. The response drives role-based UI gating, feature flags, and available products

## Seeder summary output

At completion the seeder prints a table like:

```
=== Seed Summary ===
application k-forensics          CREATED
product     kbio                  CREATED
permission  cases:read            CREATED
permission  cases:create          CREATED
...
role        k_forensics.admin     CREATED
role        k_forensics.investigator  CREATED
role        k_forensics.viewer    CREATED
group       k_forensics_admins    CREATED
group       k_forensics_investigators CREATED
role-perm   k_forensics.admin → cases:read       GRANTED
...
app-product k-forensics → kbio   LINKED
```

Re-running shows "already exists" for everything that was already seeded.
