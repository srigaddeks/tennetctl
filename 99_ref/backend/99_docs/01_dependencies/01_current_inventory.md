# Current Backend Dependency Inventory

Inventory timestamp: 2026-03-13 18:10:00 IST (+0530)

## Runtime

| Item | Version | Reviewed at | Notes |
| --- | --- | --- | --- |
| Python | CPython 3.13.5 | 2026-03-13 11:22:38 IST (+0530) | Observed from local workspace runtime |

## Python packages

Current source of truth: `backend/requirements.txt`

| Package | Exact version | Reviewed at | Used by | Purpose | Security notes | Source of truth |
| --- | --- | --- | --- | --- | --- | --- |
| `fastapi` | `0.135.1` | 2026-03-13 18:10:00 IST (+0530) | `backend/01_core/`, `backend/03_auth_manage/` | HTTP API framework and dependency injection | Keep request validation, exception handling, and dependency boundaries explicit | `backend/requirements.txt` |
| `pydantic` | `2.12.5` | 2026-03-13 18:10:00 IST (+0530) | `backend/03_auth_manage/` | Request and response schema validation | Do not expose sensitive fields by default serialization | `backend/requirements.txt` |
| `asyncpg` | `0.31.0` | 2026-03-13 18:10:00 IST (+0530) | `backend/01_core/`, `backend/03_auth_manage/` | Async PostgreSQL connection pool and query driver | Use parameterized queries only and keep pool sizes bounded | `backend/requirements.txt` |
| `authlib` | `1.6.9` | 2026-03-13 18:10:00 IST (+0530) | `backend/03_auth_manage/01_authlib/` | JWT/JOSE encoding and verification | Limit usage to JWT signing and verification boundary | `backend/requirements.txt` |
| `argon2-cffi` | `25.1.0` | 2026-03-13 18:10:00 IST (+0530) | `backend/03_auth_manage/` | Argon2id password hashing | Prefer Argon2id defaults and never log password material | `backend/requirements.txt` |
| `PyYAML` | `6.0.3` | 2026-03-13 18:10:00 IST (+0530) | `backend/01_core/`, `backend/91_scripts/` | Read numbered SQL migration files | Only load trusted repository-local migration files | `backend/requirements.txt` |
| `uvicorn` | `0.41.0` | 2026-03-13 18:10:00 IST (+0530) | `backend/main.py` | ASGI server for local and deployed runtime | Review proxy, TLS, and header configuration in deployment | `backend/requirements.txt` |
| `httpx` | `0.28.1` | 2026-03-13 18:10:00 IST (+0530) | `backend/90_tests/` | Async HTTP client and ASGI test transport | Keep test-only usage isolated from runtime code | `backend/requirements.txt` |
| `opentelemetry-api` | `1.40.0` | 2026-03-13 19:05:00 IST (+0530) | `backend/01_core/` | OpenTelemetry API surface for traces and context propagation | Keep correlation fields low-cardinality and avoid secret-bearing attributes | `backend/requirements.txt` |
| `opentelemetry-sdk` | `1.40.0` | 2026-03-13 19:05:00 IST (+0530) | `backend/01_core/` | Runtime providers for traces and OTEL log export | Exporter failures must not affect request correctness | `backend/requirements.txt` |
| `opentelemetry-exporter-otlp-proto-http` | `1.40.0` | 2026-03-13 19:05:00 IST (+0530) | `backend/01_core/` | OTLP HTTP exporter for traces and logs to a collector or backend | Keep endpoints and headers in env only; never hard-code collector credentials | `backend/requirements.txt` |
| `redis` | `5.2.1` | 2026-03-14 07:30:00 IST (+0530) | `backend/01_core/cache.py` | Async Redis/Valkey client for API response caching and pattern-based invalidation | Use `decode_responses=True`; keep CACHE_URL in env only; graceful degradation on connection failure | `backend/requirements.txt` |
| `aiosmtplib` | `5.1.0` | 2026-03-16 17:18:00 IST (+0530) | `backend/04_notifications/04_channels/email_provider.py` | Async SMTP client for email delivery | Ensure SMTP credentials are env-only; use TLS/STARTTLS | `backend/requirements.txt` |
| `pywebpush` | `2.3.0` | 2026-03-16 17:18:00 IST (+0530) | `backend/04_notifications/04_channels/webpush_provider.py` | Web Push notification delivery using VAPID | Protect VAPID private keys; keep sub mailto in env | `backend/requirements.txt` |
| `markdown` | `3.7` | 2026-03-25 13:06:00 IST (+0530) | `backend/20_ai/20_reports/service.py` | Convert Markdown to HTML for PDF generation | Only use for trusted repository-local content | `backend/requirements.txt` |
| `xhtml2pdf` | `0.2.16` | 2026-03-25 13:06:00 IST (+0530) | `backend/20_ai/20_reports/service.py` | Convert HTML to PDF | Monitor for memory usage on large reports | `backend/requirements.txt` |

## Required row format for future entries

Use this table format when packages are added:

| Package | Exact version | Reviewed at | Used by | Purpose | Security notes | Source of truth |
| --- | --- | --- | --- | --- | --- | --- |
| example-package | 1.2.3 | 2026-03-13 18:10:00 IST (+0530) | `backend/01_example/` | Short functional reason | Short risk or control note | `backend/requirements.txt` |
