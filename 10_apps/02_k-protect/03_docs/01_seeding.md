# K-Protect — Seeding Instructions

Run these steps once after a fresh tennetctl install, or any time after wiping the database.
All operations are idempotent and safe to re-run.

## Prerequisites

- tennetctl is running: `http://localhost:58000`
- DB has been migrated (includes the `11_kprotect` migrations 025–027)
- Admin credentials from the tennetctl setup wizard

## Step 1 — Boot tennetctl and run migrations

```bash
# Start tennetctl (from the tennetctl repo root)
.venv/bin/python -m uvicorn 04_backend.main:app --port 58000 --host 0.0.0.0 --reload

# In a second terminal, run the SQL migrator
.venv/bin/python -m scripts.migrator
```

Confirm that migrations `025`, `026`, and `027` appear in the migrated list.
These create the `11_kprotect` schema.

## Step 2 — Seed permissions (SQL fallback)

If the permissions API is not yet available, seed directly via SQL:

```bash
psql $DATABASE_URL -f 10_apps/02_k-protect/03_docs/03_seed/00_permissions.sql
```

This inserts 16 kprotect resource/action permission pairs into `03_iam.10_fct_permissions`.
The statement uses `ON CONFLICT DO NOTHING` and is safe to re-run.

## Step 3 — Seed the application

```bash
curl -s -X POST http://localhost:58000/v1/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_jwt>" \
  -d @10_apps/02_k-protect/03_docs/03_seed/01_application.json
```

Creates the `k-protect` application (category: `saas_web`). A 409 Conflict means it already exists — safe to skip.

## Step 4 — Seed products

```bash
for product in $(cat 10_apps/02_k-protect/03_docs/03_seed/02_products.json | python3 -c "import sys,json; [print(json.dumps(p)) for p in json.load(sys.stdin)]"); do
  curl -s -X POST http://localhost:58000/v1/products \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_jwt>" \
    -d "$product"
done
```

Creates `kprotect-engine` and `kprotect-dashboard`. 409 Conflict = already exists, skip.

## Step 5 — Seed roles

```bash
for role in $(cat 10_apps/02_k-protect/03_docs/03_seed/05_roles.json | python3 -c "import sys,json; [print(json.dumps(r)) for r in json.load(sys.stdin)]"); do
  curl -s -X POST http://localhost:58000/v1/roles \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_jwt>" \
    -d "$role"
done
```

Creates three org-tier roles: `k_protect.admin`, `k_protect.analyst`, `k_protect.viewer`.

## Step 6 — Seed groups

```bash
for group in $(cat 10_apps/02_k-protect/03_docs/03_seed/06_groups.json | python3 -c "import sys,json; [print(json.dumps(g)) for g in json.load(sys.stdin)]"); do
  curl -s -X POST http://localhost:58000/v1/groups \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_jwt>" \
    -d "$group"
done
```

Creates two default groups: `k_protect_admins`, `k_protect_analysts`.

## Step 7 — Grant role permissions

The file `03_seed/07_role_permissions.json` maps each role to its permission set.
Grant each permission via the tennetctl RBAC API:

```bash
# Example for k_protect.admin — repeat for all three roles
curl -s -X POST "http://localhost:58000/v1/roles/k_protect.admin/permissions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_jwt>" \
  -d '{"resource": "policies", "action": "read"}'
```

See `03_seed/07_role_permissions.json` for the full permission matrix.

## Step 8 — Link products to application

```bash
for link in $(cat 10_apps/02_k-protect/03_docs/03_seed/08_application_products.json | python3 -c "import sys,json; [print(json.dumps(l)) for l in json.load(sys.stdin)]"); do
  APP_CODE=$(echo $link | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['application_code'])")
  PROD_CODE=$(echo $link | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['product_code'])")
  curl -s -X POST "http://localhost:58000/v1/applications/${APP_CODE}/products" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_jwt>" \
    -d "{\"product_code\": \"${PROD_CODE}\"}"
done
```

Links `kprotect-engine` and `kprotect-dashboard` to the `k-protect` application.

## Step 9 — Issue an application token

The seeder does NOT issue application tokens — the raw token must stay in the operator's hands only.

1. Open tennetctl UI: `http://localhost:48000`
2. Navigate to: IAM → Applications → k-protect → Tokens tab
3. Click "Issue Token"
4. Copy the raw token (displayed once only — it is hashed immediately after)

## Step 10 — Start k-protect

```bash
cd 10_apps/02_k-protect && ./dev.sh
```

Backend available at `http://localhost:8200`.

## Seeder summary

After completing all steps, the following resources should exist in tennetctl:

| Type | Code | Status |
| --- | --- | --- |
| application | k-protect | CREATED |
| product | kprotect-engine | CREATED |
| product | kprotect-dashboard | CREATED |
| permission | policies:read | CREATED |
| permission | policies:create | CREATED |
| permission | policies:update | CREATED |
| permission | policies:delete | CREATED |
| permission | policies:execute | CREATED |
| permission | policy_sets:read | CREATED |
| permission | policy_sets:create | CREATED |
| permission | policy_sets:update | CREATED |
| permission | policy_sets:delete | CREATED |
| permission | decisions:read | CREATED |
| permission | library:read | CREATED |
| permission | library:install | CREATED |
| permission | evaluate:execute | CREATED |
| permission | api_keys:read | CREATED |
| permission | api_keys:create | CREATED |
| permission | api_keys:revoke | CREATED |
| role | k_protect.admin | CREATED |
| role | k_protect.analyst | CREATED |
| role | k_protect.viewer | CREATED |
| group | k_protect_admins | CREATED |
| group | k_protect_analysts | CREATED |
| app-product | k-protect → kprotect-engine | LINKED |
| app-product | k-protect → kprotect-dashboard | LINKED |

Re-running shows "already exists" (409 Conflict) for everything already seeded.
