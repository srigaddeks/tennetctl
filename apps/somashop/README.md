# somashop

Customer-facing app for **Soma Delights** — a cold-pressed juice
subscription business in Hyderabad. Built as a thin shell on top of
tennetctl + somaerp.

> Brand spec: `99_business_refs/website/.planning/REQUIREMENTS.md`
> ("Quiet luxury meets radical transparency" — greyscale UI, Outfit
> headings, Inter body, Lora pull quotes.)

## Architecture

- **Backend** (port `51740`, `apps/somashop/backend/`)
  No own DB schema. Every read/write hits tennetctl (auth, audit) or
  somaerp (catalog, subscriptions, deliveries) over HTTP.
- **Frontend** (port `51741`, `apps/somashop/frontend/`)
  Next.js 15 App Router + Tailwind 4 + Outfit/Inter/Lora typography.

## Routes (frontend)

| Path                     | Purpose                                                          |
| ------------------------ | ---------------------------------------------------------------- |
| `/`                      | Editorial home — hero, how-it-works, testimonials, FAQ           |
| `/signin`                | Mobile-OTP signup (split-screen brand panel + form)              |
| `/products`              | Subscription plans + full menu                                   |
| `/products/[slug]`       | Single product detail with target benefit + ingredients          |
| `/checkout?plan=<slug>`  | Place an order (delivery form + order summary)                   |
| `/orders`                | List of customer's subscriptions                                 |
| `/orders/[id]`           | Subscription detail — cadence, price, started, service zone      |
| `/profile`               | Account info + sign out                                          |

## Routes (backend)

| Method   | Path                              | Auth          | Purpose                                  |
| -------- | --------------------------------- | ------------- | ---------------------------------------- |
| `GET`    | `/health`                         | none          | Health check                             |
| `GET`    | `/v1/products`                    | service       | Public catalog (proxies somaerp)         |
| `GET`    | `/v1/subscription-plans`          | service       | Public plans                             |
| `GET`    | `/v1/my-orders`                   | session       | List customer's subscriptions            |
| `GET`    | `/v1/my-orders/{id}`              | session       | Single subscription (ownership-checked)  |
| `POST`   | `/v1/my-orders`                   | session       | Place order (creates customer + sub)     |

Catalog reads use somashop's **service session** (signs in at boot using
`SOMASHOP_SERVICE_EMAIL` + `SOMASHOP_SERVICE_PASSWORD`). Customer-bound
reads use the customer's bearer token.

## Run

```bash
# from repo root
set -a && . apps/somashop/.env && set +a
PYTHONPATH=. .venv/bin/python -m uvicorn apps.somashop.backend.main:app \
    --host 0.0.0.0 --port 51740 --reload

# in another shell
cd apps/somashop/frontend && npm install && npm run dev   # 51741
```

## Required env (`apps/somashop/.env`)

```
SOMASHOP_PORT=51740
SOMASHOP_FRONTEND_ORIGIN=http://localhost:51741
TENNETCTL_BASE_URL=http://localhost:51734
SOMAERP_BASE_URL=http://localhost:51736
SOMAERP_DEFAULT_ORG_ID=<org uuid>
SOMAERP_DEFAULT_WORKSPACE_ID=<workspace uuid>
SOMASHOP_SERVICE_EMAIL=<admin email>
SOMASHOP_SERVICE_PASSWORD=<admin password>
TENNETCTL_SERVICE_API_KEY=nk_...
```

## Smoke test

```bash
PYTHONPATH=. .venv/bin/python -m scripts.smoke_somashop_e2e
```

Exercises full customer journey: mobile-OTP request → verify → list
products → list plans → place order → confirm subscription appears in
`/v1/my-orders`. Generates a unique phone per run; idempotent.

## Open work

- Razorpay (or similar) payment integration — orders are created without
  payment collection in v1.
- Self-serve subscription pause / cancel.
- Product photography upload + display.
- Service zone selection (today defaults to Hyderabad).
- React Native shell sharing the same design tokens (planned).
