---
phase: 22-iam-enterprise
plan: 08
type: summary
status: complete
completed_at: 2026-04-17
---

# 22-08 Summary — SIEM Export + TOS Versioning + Password History

## What Was Built

Three bundled enterprise compliance primitives:

### 1. Audit SIEM Export (`26_siem_export/`)
Per-org destination config (webhook / S3 / Splunk HEC). Worker tails `evt_audit_outbox`, formats, delivers. Admin UI to manage destinations.

- `repository.py` — `list_destinations`, `create_destination`, `update_destination`, `delete_destination` (soft-delete)
- `service.py` — enforces org scoping, stores credentials vault_key (not inline), emits audit on create/update/delete
- `routes.py` — `GET/POST /v1/iam/siem-destinations`, `PATCH/DELETE /v1/iam/siem-destinations/{id}`
- Frontend: `/iam/security/siem/` — list + create + toggle active/inactive + delete

### 2. TOS Versioning (`27_tos/`)
Versioned Terms of Service with user acceptance tracking and mandatory re-acceptance gate on version bump.

- `repository.py` — `create_version`, `mark_effective`, `get_current`, `record_acceptance`, `check_acceptance`
- `service.py` — enforces one-active-version invariant; `tos_gate` raises 403 with `TOS_REQUIRED` code when user has no acceptance for current version
- `routes.py` — `GET /v1/tos/current`, `POST /v1/tos/versions`, `POST /v1/tos/versions/{id}/effective`, `POST /v1/tos/accept`, `GET /v1/tos/status`
- Frontend: `/iam/security/tos/` — version list + activate + user acceptance status

### 3. Password History
Prevents reuse of the last N passwords (N from AuthPolicy `password.history_depth` vault key).

- `repository.py` in `08_credentials/` — `record_password_hash`, `get_recent_hashes`, `prune_old_hashes`
- `service.py` in `08_credentials/` — checks argon2id against recent hashes on password change; records new hash after change; prunes beyond depth

## Tests
- `tests/test_siem_export.py` — list empty, create webhook, invalid kind, update, delete
- `tests/test_tos.py` — no current TOS, create version, mark effective, accept, gate check before/after acceptance
- `tests/test_password_history.py` — reuse rejected, unique accepted, history disabled when depth=0, pruning beyond depth

## Decisions

- SIEM credentials stored as vault key reference, never inline in DB
- TOS gate returns `{"ok": false, "error": {"code": "TOS_REQUIRED"}}` — frontend redirects to acceptance page
- Password history depth of 0 disables the check entirely (no overhead)
- History pruning runs in same tx as password update
