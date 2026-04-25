# TennetCTL Dev Credentials + Stack Map

The Soma Delights stack runs as **4 backends + 4 frontends + Postgres + supporting infra**.

## Live URLs

| App         | Backend                 | Frontend                | Purpose                                            |
| ----------- | ----------------------- | ----------------------- | -------------------------------------------------- |
| tennetctl   | http://localhost:51734  | http://localhost:51735  | Platform: IAM, audit, vault, notify, monitoring, feature flags, product_ops |
| somaerp     | http://localhost:51736  | http://localhost:51737  | Back-office ERP — kitchens, recipes, production, customers, deliveries |
| somacrm     | http://localhost:51738  | http://localhost:51739  | CRM — contacts, deals, pipeline, activities, reports |
| somashop    | http://localhost:51740  | http://localhost:51741  | **Customer-facing app** — mobile-OTP signup, browse menu, place orders |

Health-check any backend: `curl http://localhost:<port>/health`.

## Admin credentials (tennetctl + somaerp + somacrm)

```
Email:    sri@tennetctl.dev
Password: DevPass123!
```

Used by all back-office apps. Also the "service identity" somashop signs in as
on boot (so it can read tenant-scoped catalog data on behalf of customers).

## Customer credentials (somashop)

Customers self-serve via mobile OTP — no shared password. The dev stack runs
in **stub mode** (no Twilio configured), so the OTP request returns the code
in the response body as `debug_code`. Real Twilio flips on automatically once
`sms.twilio.{account_sid,auth_token,from_number}` are stored in vault.

## Database

- DSN: `postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl`
- All four apps share this Postgres. Schemas:
  - `03_iam`, `04_audit`, `02_vault`, etc. — tennetctl
  - `11_somaerp` — ERP
  - `12_somacrm` — CRM
  - somashop owns no schema (proxies everything)

## Vault root key (rotate before prod)

```
TENNETCTL_VAULT_ROOT_KEY=Gjpz8p/6Zy48sIkudpnebaGgvGH7vhJuGyeh06IHPk0=
```

## Modules enabled (tennetctl)

`core, iam, audit, featureflags, vault, notify, monitoring, social_publisher, social_capture, product_ops`

## Boot sequence

```bash
# Stack root: /Users/sri/Documents/tennetctl
cd /Users/sri/Documents/tennetctl

# 1. Postgres + supporting infra (already running via docker compose):
docker ps  # confirm postgres + valkey + nats + minio + apisix + qdrant

# 2. tennetctl backend
.venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0 --reload

# 3. tennetctl frontend
cd frontend && npm run dev  # 51735

# 4. somaerp backend
set -a && . apps/somaerp/.env && set +a
PYTHONPATH=. .venv/bin/python -m uvicorn apps.somaerp.backend.main:app --host 0.0.0.0 --port 51736 --reload

# 5. somaerp frontend
cd apps/somaerp/frontend && npm run dev  # 51737

# 6. somacrm backend
set -a && . apps/somacrm/.env && set +a
PYTHONPATH=. .venv/bin/python -m uvicorn apps.somacrm.backend.main:app --host 0.0.0.0 --port 51738 --reload

# 7. somacrm frontend
cd apps/somacrm/frontend && npm run dev  # 51739

# 8. somashop backend
set -a && . apps/somashop/.env && set +a
PYTHONPATH=. .venv/bin/python -m uvicorn apps.somashop.backend.main:app --host 0.0.0.0 --port 51740 --reload

# 9. somashop frontend
cd apps/somashop/frontend && npm run dev  # 51741
```

## Smoke tests

```bash
# Full pytest suite (real DB, no mocks)
.venv/bin/pytest tests/ -v

# End-to-end customer flow (live stack required)
PYTHONPATH=. .venv/bin/python -m scripts.smoke_somashop_e2e

# Re-seed Soma Delights catalog (idempotent)
PYTHONPATH=. .venv/bin/python -m scripts.seed_soma_catalog
```

## Process management gotcha

To stop a server bound to a port, **never** use the naive
`lsof -ti :PORT | xargs kill`. That returns every PID with *any* TCP
connection to that port — including remote clients that just happen to
have a CLOSED connection. Killing those cascades into unrelated services
(e.g., killing a CRM client connection accidentally killed the tennetctl
backend during this session).

Use the LISTEN-only filter:

```bash
# Safe — only the listening server process
lsof -ti :51734 -sTCP:LISTEN | xargs kill 2>/dev/null
```

Or just identify the uvicorn parent and `kill -TERM` that PID directly.

## Brand spec

`99_business_refs/website` is the brand source of truth.

- Type: **Outfit** (headings) + **Inter** (body) + **Lora** (pull quotes) +
  **JetBrains Mono** (data).
- Palette: stone greyscale (--grey-0..900). Color reserved for product
  photography + status semantics. No decorative blue/teal/purple anywhere.
- Tagline: "Quiet luxury meets radical transparency."
- Layout: 1200px max content width, 680px max reading width.

All 4 frontends pull from this spec. Customer-facing somashop is the most
literal interpretation; somacrm + somaerp adapt the same tokens for an
operator-grade density.

---

## What's working end-to-end

- **Customer signup**: `/signin` on somashop → mobile OTP → verify → returns to home with `Test Customer` shown in topbar.
- **Browse menu**: `/products` lists 3 plans + 10 real Soma Delights products with descriptions, benefits, INR prices.
- **Product detail**: `/products/[slug]` shows individual product with editorial layout (pull quote benefit + price + CTA).
- **Checkout**: `/checkout?plan=<slug>` form — collects name/phone/address, places order via somashop backend. Creates a somaerp customer + subscription.
- **Orders**: `/orders` shows the customer's subscriptions with status badges.
- **Profile**: `/profile` account info + sign out.
- **Audit emission**: every CRM/ERP mutation surfaces in `/v1/audit-events`.
- **Mobile OTP**: in tennetctl, reusable by every app.
- **Roles seeded**: 7 standard roles (kitchen_staff, rider, ops_manager, erp_admin, crm_viewer, crm_sales_rep, crm_admin) + 28 permissions.
