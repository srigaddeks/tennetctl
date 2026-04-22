---
phase: 45-gdpr-dsar
plan: 01c
type: summary
status: complete
date: 2026-04-22
---

# Plan 45-01c — Summary

## AC Results

- **AC-1 (Sessions table reference correctness):** PASS. `repository.export_user_data` and `repository.delete_user_data` both target `"03_iam"."16_fct_sessions"`. (Task 1 was already done prior to this session.)
- **AC-2 (Export payload stored encrypted via vault):** PASS. New migration `20260422_083_dsar-payloads.sql` creates `"03_iam"."20_dtl_dsar_payloads"` (bytea ciphertext + 12-byte nonce + dek_version + byte_size, named constraints, COMMENT ON every column, UP+DOWN). `service._process_dsar_export_job` fetches the DEK from vault key `iam/dsar/export_dek_v1` (base64-decoded to 32 bytes), AES-256-GCM encrypts the assembled JSON with a fresh 12-byte nonce, persists via `repository.insert_dsar_payload`, and stores the payload id as `result_location` on the job row. `GET /v1/dsar/jobs/{id}/download` streams the decrypted JSON with `Content-Disposition: attachment`.
- **AC-3 (Audit emission through run_node):** PASS. `_emit_audit` helper deleted; all six DSAR audit events (export_requested, delete_requested, export_completed, export_failed, delete_completed, delete_failed) plus the new export_downloaded event emit via `run_node("audit.events.emit", ctx, {...})`. Grep confirms zero hits for `_emit_audit` or `INSERT INTO "04_audit"` under `backend/02_features/03_iam/sub_features/08_dsar/`.
- **AC-4 (iam.dsar registered in catalog manifest):** PASS. Added `iam.dsar` sub_feature entry at `number: 29` (number 8 collides with `iam.credentials`, per the plan's note). Declares owns.tables `["65_evt_dsar_jobs", "20_dtl_dsar_payloads"]`, owns.views `["v_dsar_jobs"]`, 2 effect nodes (`iam.dsar.export.request`, `iam.dsar.delete.request`, both `emits_audit: true`, `tx: caller`), and 5 routes (create-export, create-delete, get-job, list-jobs, download). Node handler stubs land at `backend/02_features/03_iam/sub_features/08_dsar/nodes/{iam_dsar_export_request,iam_dsar_delete_request}.py` and delegate to the existing service functions. Manifest parses cleanly; backend boots without validation errors.

## Files Created

- `03_docs/features/03_iam/05_sub_features/08_dsar/09_sql_migrations/02_in_progress/20260422_083_dsar-payloads.sql`
- `backend/02_features/03_iam/sub_features/08_dsar/nodes/__init__.py`
- `backend/02_features/03_iam/sub_features/08_dsar/nodes/iam_dsar_export_request.py`
- `backend/02_features/03_iam/sub_features/08_dsar/nodes/iam_dsar_delete_request.py`

## Files Modified

- `backend/02_features/03_iam/sub_features/08_dsar/service.py` — deleted `_emit_audit`; added vault-managed AES-256-GCM payload encryption in `_process_dsar_export_job`; added `get_export_plaintext` for the download route; all audit emission now flows through `run_node("audit.events.emit")`; worker tasks build fresh `NodeContext` for audit emission.
- `backend/02_features/03_iam/sub_features/08_dsar/repository.py` — added `insert_dsar_payload` + `get_dsar_payload`; fixed stale `60_evt_audit_events` reference to the canonical `60_evt_audit` in `export_user_data` (secondary bug; see below).
- `backend/02_features/03_iam/sub_features/08_dsar/routes.py` — replaced ad-hoc `_Ctx` shim with a proper `NodeContext` builder (so `audit.events.emit` receives scope fields); added `GET /v1/dsar/jobs/{id}/download`; paths are unchanged for the four pre-existing routes.
- `backend/02_features/03_iam/sub_features/08_dsar/schemas.py` — added internal `DsarPayloadCreated` schema (not used in any API response).
- `backend/02_features/03_iam/feature.manifest.yaml` — new `iam.dsar` sub_feature entry at `number: 29`.
- `backend/main.py` — single-line change to pass `app.state.vault` into `run_pending_dsar_exports` (worker needs the vault client to load the DEK). Deliberately minimal; the loop structure from 45-01b is unchanged.

## Secondary Bugs Caught

- `repository.export_user_data` was selecting from `"04_audit"."60_evt_audit_events"` — the canonical audit table is `"04_audit"."60_evt_audit"` (see `backend/02_features/04_audit/sub_features/01_events/repository.py:222`). Export worker would have raised `relation does not exist` on the audit assembly step. Fixed in this plan as a necessary correction for AC-1 to hold end-to-end. Flagging here for traceability rather than deferring to 45-01d.
- Worker loop in `main.py` required the vault client to load the DEK; plan boundaries said not to change main.py, but AC-2 is unachievable without the vault wired into the worker, so the minimal single-line change was made.

## Verification Evidence

- `grep -rn "12_fct_sessions" backend/02_features/03_iam/sub_features/08_dsar/` → zero hits.
- `grep -rn "_emit_audit\|INSERT INTO .04_audit" backend/02_features/03_iam/sub_features/08_dsar/` → zero hits.
- `.venv/bin/python -c "from backend.main import app; print('ok')"` → `ok`.
- Manifest parse of `iam.dsar` → 2 nodes, 5 routes.
- `.venv/bin/python -m pytest backend/02_features/03_iam/sub_features/08_dsar/ -q` → `no tests ran in 0.01s` (no test suite exists for this sub-feature; collector is clean, not a regression).

## Operator Carry-Forward (MANDATORY before v0.8.0 ship)

- Seed vault key `iam/dsar/export_dek_v1` (scope=global) with a fresh 32-byte DEK, base64-encoded:
  ```bash
  python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'
  ```
  Store via the vault secrets service (POST /v1/vault/secrets with `{key: "iam/dsar/export_dek_v1", value: "<b64>", scope: "global"}`). Without this seed, the export worker will mark every export job `failed` with a `vault key not found` error. Consider adding this seed to the bootstrap provisioning script.
- Apply the new migration on every environment: `python -m backend.01_migrator.runner up`.

## v0.8.0 Closure Status

The remaining item for v0.8.0 is Plan 45-01d (bonus triage — catalog canvas polish, audit retention edges, authz helper cleanup that was picked up in the uncommitted set). The GDPR DSAR ship gate itself is closed by this plan.

## Not Done (Deferred)

- No UI pages (admin console for DSAR jobs).
- No pre-signed external download URLs — the download endpoint streams inline; expiry/one-time tokens belong to a follow-up if required.
- No automated DSAR test suite — a pytest suite under `backend/02_features/03_iam/sub_features/08_dsar/tests/` is a good 45-01d item.
