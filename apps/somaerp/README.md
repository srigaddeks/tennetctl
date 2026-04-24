# somaerp

Generic multi-kitchen, multi-region ERP for product businesses. Built on
tennetctl primitives (auth, IAM, audit, vault, notify) consumed over HTTP.
First tenant: Soma Delights.

## Architecture

- Backend: FastAPI on port `51736`, `apps/somaerp/backend/`
- Frontend: Next.js on port `51737`, `apps/somaerp/frontend/`
- Database: shared tennetctl Postgres (port `5434`), schema `"11_somaerp"`
- Tennetctl proxy: all auth / IAM / audit / vault / notify calls forwarded
  to tennetctl on port `51734` via `01_core/tennetctl_client.py`

## Run

```bash
# Backend (from repo root)
cd apps/somaerp/backend
pip install -r requirements.txt
SOMAERP_PG_PASS=tennetctl_dev \
TENNETCTL_SERVICE_API_KEY=nk_your_service_key \
PYTHONPATH=../../.. \
  python -m uvicorn apps.somaerp.backend.main:app \
    --host 0.0.0.0 --port 51736 --reload

# Frontend
cd apps/somaerp/frontend
npm install
npm run dev   # http://localhost:51737
```

### Environment variables

| Var | Default | Required |
| --- | --- | --- |
| `SOMAERP_PG_HOST` | `localhost` | no |
| `SOMAERP_PG_PORT` | `5434` | no |
| `SOMAERP_PG_USER` | `tennetctl` | no |
| `SOMAERP_PG_PASS` | `tennetctl_dev` | yes (in non-default envs) |
| `SOMAERP_PG_DB` | `tennetctl` | no |
| `SOMAERP_PORT` | `51736` | no |
| `SOMAERP_DEBUG` | `false` | no |
| `SOMAERP_FRONTEND_ORIGIN` | `http://localhost:51737` | no |
| `TENNETCTL_BASE_URL` | `http://localhost:51734` | no |
| `TENNETCTL_SERVICE_API_KEY` | — | yes (system-scoped calls) |

## Migrations

somaerp delegates to the tennetctl migrator. Migrations live under
`apps/somaerp/03_docs/features/11_somaerp/05_sub_features/*/09_sql_migrations/`.

```bash
cd apps/somaerp/backend
PYTHONPATH=../../.. python -m scripts.migrator apply
PYTHONPATH=../../.. python -m scripts.migrator status
```

## Tests

```bash
# From repo root
PYTHONPATH=. .venv/bin/python -m pytest apps/somaerp/backend/tests/ -v
```

The smoke tests stub the tennetctl client and skip the lifespan, so no
live Postgres or live tennetctl process is required.

## Documentation

Architecture, ADRs, data model, API design, scaling, integration, Soma
Delights tenant config — start here:

- `apps/somaerp/03_docs/00_main/00_overview.md`
