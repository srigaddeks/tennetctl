---
phase: 21-iam-oss-completion
plan: 05
status: complete
completed_at: 2026-04-17
---

# 21-05 Summary — GDPR Data Export + Erasure

## What Was Built

GDPR Articles 15 (data export) and 17 (right to erasure) implemented as self-serve primitives.

## Files Created / Modified

### Migration
- `03_docs/features/03_iam/05_sub_features/19_gdpr/09_sql_migrations/01_migrated/20260417_056_iam-gdpr-jobs.sql`
  - `01_dim_gdpr_kinds` (export, erase)
  - `02_dim_gdpr_statuses` (queued, processing, completed, failed, cancelled)
  - `10_fct_gdpr_jobs` (id, user_id, kind_id, status_id, hard_erase_at, download_url_hash)

### Backend sub-feature (`backend/02_features/03_iam/sub_features/19_gdpr/`)
- `__init__.py` — package marker
- `schemas.py` — ExportRequestIn, EraseRequestIn (password + totp_code + confirm="DELETE"), GdprJobOut, GdprStatusOut
- `repository.py` — insert_job, get_job, get_latest_by_user_kind, update_job_status, list_queued_exports, list_due_erasures
- `service.py` — request_export, request_erasure (inline pseudonymization), assemble_bundle, _hard_purge_user_pii (nulls actor_user_id in evt_audit), gdpr_worker_loop
- `routes.py` — POST /v1/account/data-export, POST /v1/account/delete-me, GET /v1/account/gdpr/status

### Registration
- `backend/02_features/03_iam/routes.py` — gdpr router registered
- `backend/main.py` — gdpr_worker_loop started as asyncio task in lifespan

### Frontend
- `frontend/src/app/(dashboard)/account/privacy/page.tsx` — "Download my data" + "Delete my account" modal with password / TOTP / type-DELETE confirm

### Tests
- `tests/test_iam_gdpr.py` — 5 tests, all green:
  - test_export_job_created — job inserted with kind=export, status=queued
  - test_assemble_bundle_keys — bundle contains user, sessions, memberships, audit_events
  - test_erasure_pseudonymizes_user — email replaced with deleted-{uuid}@removed.local
  - test_erasure_blocks_signin — signin fails after pseudonymization
  - test_gdpr_status — GET /v1/account/gdpr/status returns export/erase jobs

## Key Design Decisions

- **No dependency on 21-04**: erasure pseudonymization is inlined directly in service.py
- **Hard purge**: nullifies `actor_user_id` and PII metadata keys from `60_evt_audit` rows (rows preserved, PII removed) — run after `hard_erase_at`
- **Storage v0.1.6**: local filesystem (`/tmp/tennetctl_gdpr_exports/{job_id}.json`); `gdpr.storage_kind` config key reserved for S3 opt-in
- **Worker**: asyncio task polling every 60s for queued exports and due erasures
- **Recovery window**: 30 days (`hard_erase_at = now() + 30d`); cancellation sets status=cancelled (recovery flow is future scope)

## Test Results

```
5 passed, 3 warnings in 3.45s
```

Warnings are only `datetime.utcnow()` deprecation notices — not bugs.
