---
phase: 45-gdpr-dsar
plan: 01c
type: execute
wave: 1
depends_on: ["45-01b"]
files_modified:
  - backend/02_features/03_iam/sub_features/08_dsar/service.py
  - backend/02_features/03_iam/sub_features/08_dsar/repository.py
  - backend/02_features/03_iam/sub_features/08_dsar/schemas.py
  - backend/02_features/03_iam/feature.manifest.yaml
  - 03_docs/features/03_iam/05_sub_features/08_dsar/09_sql_migrations/02_in_progress/
autonomous: true
---

<objective>
## Goal
Close the v0.8.0 DSAR ship gate: encrypt export payloads via vault-managed keys, route audit emission through `run_node`, register DSAR sub-feature in the catalog manifest, and fix the broken sessions-table reference in export/delete queries.

## Purpose
45-01b verified plumbing end-to-end but left four items blocking production ship:
1. Export payloads are never stored (only a fake `vault_path` is persisted) — GET /dsar-jobs/{id}/download cannot return anything.
2. Audit emission bypasses the node contract — the whole point of ADR-018 is broken for DSAR.
3. DSAR nodes/routes aren't in the IAM manifest — `run_node("iam.dsar.*")` would fail and catalog UI shows nothing.
4. Data-collection queries hit `"03_iam"."12_fct_sessions"` (wrong); the real table is `"03_iam"."16_fct_sessions"`. Worker always fails.

## Output
- DSAR exports stored as AES-256-GCM ciphertext in a new `22_dtl_dsar_payloads` table; DEK fetched from vault key `iam/dsar/export_dek_v1`.
- `_emit_audit` deleted; all DSAR audit events emitted via `run_node("audit.events.emit", ...)`.
- `iam.dsar` sub-feature entry added to `backend/02_features/03_iam/feature.manifest.yaml` (routes + nodes + owns).
- Both `export_user_data` and `delete_user_data` reference `16_fct_sessions`.
</objective>

<context>
@.paul/PROJECT.md
@.paul/STATE.md
@.paul/phases/45-gdpr-dsar/45-01b-SUMMARY.md

## Source Files
@backend/02_features/03_iam/sub_features/08_dsar/service.py
@backend/02_features/03_iam/sub_features/08_dsar/repository.py
@backend/02_features/03_iam/sub_features/08_dsar/schemas.py
@backend/02_features/03_iam/feature.manifest.yaml
@backend/02_features/02_vault/client.py

## Prior Decisions in Play
- Phase 7: AES-256-GCM envelope encryption via PyCA cryptography; per-secret DEK + 12-byte nonce + GCM auth tag.
- Phase 3 Plan 03: effect-must-emit-audit triple-defense; audit scope mandatory (user_id + session_id + org_id + workspace_id) with two bypasses (setup category, failure outcome).
- Phase 45-01 discovery: effect nodes have no emit_audit bypass — must route through run_node.
</context>

<acceptance_criteria>

## AC-1: Sessions table reference correctness
```gherkin
Given a DSAR export or delete job is processed by the worker
When repository.export_user_data or repository.delete_user_data executes
Then every query targets "03_iam"."16_fct_sessions" (not "12_fct_sessions")
And the worker completes a synthetic test job without the previous "relation does not exist" failure
```

## AC-2: Export payload stored encrypted via vault
```gherkin
Given a DSAR export job transitions from in_progress to completed
When export_user_data assembles the payload
Then the JSON is AES-256-GCM encrypted using a DEK fetched from vault key "iam/dsar/export_dek_v1"
And the ciphertext + nonce are persisted to "03_iam"."22_dtl_dsar_payloads" keyed by job_id
And fct_dsar_jobs.result_location stores the dtl row id (not a fake path)
And GET /v1/dsar-jobs/{id}/download returns a pre-signed time-boxed URL that decrypts and streams the JSON
```

## AC-3: Audit emission goes through run_node
```gherkin
Given any DSAR service function (create_export_request, create_delete_request, worker transitions) emits audit
When the emit happens
Then it calls run_node("audit.events.emit", ctx=..., inputs=...) — never a direct SQL INSERT
And the private _emit_audit helper in service.py is removed
And evt_audit_events rows continue to appear with correct category/outcome/scope for the 4 existing DSAR event keys
```

## AC-4: DSAR sub-feature registered in catalog manifest
```gherkin
Given backend boot loads backend/02_features/03_iam/feature.manifest.yaml
When the manifest parser runs
Then an "iam.dsar" sub-feature exists with:
  - owns.schema "03_iam", owns.tables ["18_fct_dsar_jobs", "22_dtl_dsar_payloads"]
  - owns.views ["v_dsar_jobs"] (if view exists) or []
  - 4 routes matching existing DSAR endpoints (create export, create delete, get job, download)
  - At minimum 2 effect nodes: iam.dsar.export.request, iam.dsar.delete.request (both emits_audit: true, tx: caller)
And /catalog UI shows the iam.dsar sub-feature with its nodes and routes
And the cross-import linter + manifest Pydantic validator both pass
```

</acceptance_criteria>

<tasks>

<task type="auto">
  <name>Task 1: Fix sessions table name in DSAR repository</name>
  <files>backend/02_features/03_iam/sub_features/08_dsar/repository.py</files>
  <action>
    Replace both occurrences of `"03_iam"."12_fct_sessions"` with `"03_iam"."16_fct_sessions"`:
    - repository.py:200 — SELECT in export_user_data
    - repository.py:248 — DELETE in delete_user_data
    Verify against feature.manifest.yaml iam.sessions owns block (table is 16_fct_sessions) and .claude/rules/common/database.md fct_* numbering.
    Do not touch any other table names in this task.
  </action>
  <verify>grep -n "fct_sessions" backend/02_features/03_iam/sub_features/08_dsar/repository.py shows only 16_fct_sessions (2 hits, zero 12_fct_sessions hits)</verify>
  <done>AC-1 satisfied: both sites reference the correct sessions table.</done>
</task>

<task type="auto">
  <name>Task 2: Add dtl_dsar_payloads table + vault-encrypted payload storage</name>
  <files>
    03_docs/features/03_iam/05_sub_features/08_dsar/09_sql_migrations/02_in_progress/{YYYYMMDD}_{NNN}_dsar-payloads.sql,
    backend/02_features/03_iam/sub_features/08_dsar/repository.py,
    backend/02_features/03_iam/sub_features/08_dsar/service.py,
    backend/02_features/03_iam/sub_features/08_dsar/schemas.py
  </files>
  <action>
    Migration — create `"03_iam"."22_dtl_dsar_payloads"`:
    - id UUID v7 PK, job_id UUID NOT NULL REFERENCES "03_iam"."18_fct_dsar_jobs"(id) UNIQUE
    - ciphertext BYTEA NOT NULL, nonce BYTEA NOT NULL (12 bytes), dek_version SMALLINT NOT NULL DEFAULT 1
    - byte_size INT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    - Named constraints (pk_, fk_, uq_). COMMENT ON every column. UP + DOWN sections. Global NNN.

    Service (service.py::run_export_job):
    - Replace the `vault_path = f"dsar/{job_id}/export.json"` stub.
    - Fetch DEK: `dek_b64 = await vault_client.get("iam/dsar/export_dek_v1")` (seeded by operator; document in SUMMARY).
    - Encrypt `json.dumps(data, default=str).encode()` with AES-256-GCM (PyCA cryptography, same primitive as backend/02_features/02_vault) — 12-byte random nonce.
    - Call new repository.insert_dsar_payload(conn, job_id, ciphertext, nonce, dek_version=1, byte_size=len(plaintext)) returning the dtl row id.
    - Pass that id as result_location into update_dsar_job_status.

    Download endpoint (routes.py::get_dsar_job_download or equivalent):
    - Read dtl row by job_id, fetch DEK, decrypt, stream as application/json with Content-Disposition.
    - Audit the download via run_node (piggy-backs Task 3).
    - If payload row missing, 404 with code NOT_READY.

    schemas.py: add DsarPayloadCreated internal schema; do not leak ciphertext to API responses.

    Avoid: putting plaintext in the DB, storing DEK in the row, rolling our own crypto — reuse AESGCM from cryptography.hazmat.primitives.ciphers.aead.
  </action>
  <verify>
    1) Migrator applies the new migration clean on an empty branch DB.
    2) Integration test: create export job → worker runs → dtl_dsar_payloads has 1 row with non-empty ciphertext, result_location on fct = dtl row id.
    3) GET /v1/dsar-jobs/{id}/download returns decrypted JSON with same keys the worker assembled.
  </verify>
  <done>AC-2 satisfied: export payloads are AES-GCM encrypted with vault-managed DEK and retrievable via the download endpoint.</done>
</task>

<task type="auto">
  <name>Task 3: Route DSAR audit emission through run_node</name>
  <files>backend/02_features/03_iam/sub_features/08_dsar/service.py</files>
  <action>
    Delete the private `_emit_audit` helper (service.py:357–392) that INSERTs directly into 60_evt_audit_events.

    Replace every call site with:
    ```python
    _run_node = import_module("backend.01_catalog.runner").run_node
    await _run_node(
        pool,
        "audit.events.emit",
        ctx=ctx,
        inputs={
            "event_key": "iam.dsar.export.requested",  # etc
            "category": "iam",
            "outcome": "success",  # or "failure"
            "metadata": {...},
        },
    )
    ```
    Audit scope (user_id/session_id/org_id/workspace_id) comes from ctx — do not pass it inline.

    Call sites to update (based on grep for `_emit_audit(`):
    - create_export_request success path (iam.dsar.export.requested)
    - create_delete_request success path (iam.dsar.delete.requested)
    - run_export_job completed (iam.dsar.export.completed) / failed (iam.dsar.export.failed)
    - run_delete_job completed (iam.dsar.delete.completed) / failed (iam.dsar.delete.failed)
    - download endpoint (iam.dsar.export.downloaded) — added in Task 2

    Avoid: direct INSERT INTO evt_audit_events anywhere in the DSAR sub-feature. If any path needs to skip audit (it shouldn't), document why inline.
  </action>
  <verify>
    1) `grep -rn "_emit_audit\|60_evt_audit_events" backend/02_features/03_iam/sub_features/08_dsar/` returns zero hits.
    2) Integration run of one export job produces evt_audit_events rows with actor_user_id + session_id + org_id populated from ctx.
    3) Pytest DSAR suite still collects + passes.
  </verify>
  <done>AC-3 satisfied: all DSAR audit goes through run_node("audit.events.emit", ...).</done>
</task>

<task type="auto">
  <name>Task 4: Register iam.dsar in feature manifest</name>
  <files>backend/02_features/03_iam/feature.manifest.yaml</files>
  <action>
    Add a new sub_feature entry under spec.sub_features (insert in numeric order — use number: 8):

    ```yaml
    - key: iam.dsar
      number: 8
      label: GDPR DSAR
      description: Operator-triggered data subject access (export) and erasure (delete) jobs. Background worker transitions jobs through requested → in_progress → completed/failed; export payloads are AES-256-GCM encrypted with a vault-managed DEK and stored in dtl_dsar_payloads.
      owns:
        schema: "03_iam"
        tables: ["18_fct_dsar_jobs", "22_dtl_dsar_payloads"]
        views: []   # adjust if v_dsar_jobs exists on disk
        seeds: []
      nodes:
        - key: iam.dsar.export.request
          kind: effect
          handler: sub_features.08_dsar.nodes.iam_dsar_export_request.DsarExportRequest
          label: Request DSAR Export
          description: Enqueues a DSAR export job at status=requested; emits audit iam.dsar.export.requested.
          emits_audit: true
          version: 1
          tags: [gdpr, dsar, write]
          execution: {timeout_ms: 5000, retries: 0, tx: caller}
        - key: iam.dsar.delete.request
          kind: effect
          handler: sub_features.08_dsar.nodes.iam_dsar_delete_request.DsarDeleteRequest
          label: Request DSAR Delete
          description: Enqueues a DSAR delete job at status=requested; emits audit iam.dsar.delete.requested.
          emits_audit: true
          version: 1
          tags: [gdpr, dsar, write]
          execution: {timeout_ms: 5000, retries: 0, tx: caller}
      routes:
        - method: POST
          path: /v1/dsar-jobs/export
          handler: sub_features.08_dsar.routes.create_export_request_route
        - method: POST
          path: /v1/dsar-jobs/delete
          handler: sub_features.08_dsar.routes.create_delete_request_route
        - method: GET
          path: "/v1/dsar-jobs/{id}"
          handler: sub_features.08_dsar.routes.get_dsar_job_route
        - method: GET
          path: "/v1/dsar-jobs/{id}/download"
          handler: sub_features.08_dsar.routes.get_dsar_job_download_route
      ui_pages: []
    ```

    Adjust route handler names to match the actual symbols in backend/02_features/03_iam/sub_features/08_dsar/routes.py (check before writing). If iam.sub-feature number 8 is already taken (credentials was 8 in some revisions — file shows iam.credentials: 8; use next free number like 29 to avoid collision; preserve permanence rule).

    Create thin node handler stubs at backend/02_features/03_iam/sub_features/08_dsar/nodes/iam_dsar_export_request.py and iam_dsar_delete_request.py that delegate to the existing service.create_export_request / create_delete_request so emits_audit=true is honest.

    Avoid: renaming existing sub-feature numbers; changing any other sub_features entry.
  </action>
  <verify>
    1) Backend boots without manifest validation errors (`cd tennetctl && .venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0`).
    2) /catalog or the catalog inspection endpoint lists iam.dsar with 2 nodes + 4 routes.
    3) Cross-import linter passes.
  </verify>
  <done>AC-4 satisfied: iam.dsar registered in catalog, handlers resolvable, no validator errors.</done>
</task>

</tasks>

<boundaries>

## DO NOT CHANGE
- Any other sub-feature entry in feature.manifest.yaml (don't renumber credentials/sessions/auth).
- Migration `071_iam-dsar.sql` already applied — Task 2 creates a NEW migration for dtl_dsar_payloads; never edit a migrated file.
- The worker loop wiring in main.py (45-01b closed it).
- Other files in the git-staged uncommitted set (catalog canvas, iam enterprise surfaces, etc.) — that cleanup belongs to 45-01d.
- Audit retention + authz helpers out-of-scope additions from 45-01 — triage in 45-01d.

## SCOPE LIMITS
- No new admin UI pages for DSAR in this plan (UI wiring is a follow-up phase).
- No cascade-rewrite of delete_user_data beyond the sessions-table fix (other reference queries that may have similar drift are not in this plan's AC — flag in SUMMARY if found).
- No SDK updates.
- No operator-facing docs beyond the SUMMARY.

</boundaries>

<verification>
Before declaring plan complete:
- [ ] `grep -n "12_fct_sessions" backend/02_features/03_iam/sub_features/08_dsar/` returns zero hits.
- [ ] `grep -rn "_emit_audit\|INSERT INTO .04_audit" backend/02_features/03_iam/sub_features/08_dsar/` returns zero hits.
- [ ] New migration applies UP then DOWN cleanly on a fresh DB.
- [ ] `.venv/bin/python -m pytest backend/02_features/03_iam/sub_features/08_dsar/tests/ -q` passes (10+ tests).
- [ ] Backend boots clean; manifest parser accepts iam.dsar entry.
- [ ] Manual live run: create one export job, watch worker complete it, GET /download returns decrypted JSON; evt_audit rows populated for requested + completed + downloaded.
- [ ] All 4 ACs explicitly checked off in SUMMARY.
</verification>

<success_criteria>
- All 4 tasks complete, all 4 ACs verified on the running stack.
- `cd tennetctl && .venv/bin/python -m pytest` green for the DSAR suite.
- Zero direct audit INSERTs in DSAR code; zero references to 12_fct_sessions.
- v0.8.0 ship gate unblocked — only remaining item is 45-01d (bonus triage).
</success_criteria>

<output>
After completion, create `.paul/phases/45-gdpr-dsar/45-01c-SUMMARY.md` documenting:
- What shipped per AC
- Any secondary bugs caught during live verification
- Confirmation that 45-01d (bonus triage) is the final remaining item for v0.8.0 closure
- Operator carry-forward: seed vault key `iam/dsar/export_dek_v1` with 32 bytes base64 before first export job
</output>
