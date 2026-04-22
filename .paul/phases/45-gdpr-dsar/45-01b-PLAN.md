---
phase: 45-gdpr-dsar
plan: 01b
type: execute
wave: 1
depends_on: ["45-01"]
files_modified:
  - 03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/02_in_progress/20260421_071_iam-dsar.sql
  - 03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/seeds/03iam_dsar_types.yaml
  - 03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/seeds/03iam_dsar_statuses.yaml
  - backend/09_sql_migrations/20260421_071_dsar.sql
  - tests/test_iam_dsar.py
  - backend/main.py
autonomous: true
---

<objective>
## Goal
Make Plan 45-01 actually runnable. Align migration ↔ repository ↔ tests on a single schema design (the numbered/dim-table design the repository already expects), wire the DSAR worker loop into the backend lifespan so jobs transition off `requested`, and re-seat the migration in the per-sub-feature location so it is discovered correctly.

## Purpose
Plan 45-01 shipped code across 6 commits but in a state that cannot execute: the migration creates a table at one path/shape, the repository queries a different path/shape with dim tables that are never created, and tests call repo functions with a signature that doesn't exist. Job workers also aren't wired, so even if the rest worked, jobs would stall at `status='requested'` forever. v0.8.0 cannot gate on DSAR until this runs.

## Output
- New migration `03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/02_in_progress/20260421_071_iam-dsar.sql` creating `07_dim_dsar_statuses`, `08_dim_dsar_types`, `65_evt_dsar_jobs` with columns matching `repository.py`.
- Seed YAMLs for the two dim tables under the same sub-feature's `seeds/` dir.
- The old monolithic `backend/09_sql_migrations/20260421_071_dsar.sql` removed (superseded).
- `tests/test_iam_dsar.py` rewritten: fixtures match the real IAM schema (`12_fct_users.id`, `account_type_id`, `created_by`, `updated_by`; EAV for email via `dtl_user_attrs`); repo calls use keyword arguments; tests actually runnable under pytest.
- `backend/main.py` lifespan invokes `run_pending_dsar_exports` and `run_pending_dsar_deletes` in the existing background loop pattern.
</objective>

<context>
## Project Context
@.paul/PROJECT.md
@.paul/ROADMAP.md
@.paul/STATE.md

## Prior Work
@.paul/phases/45-gdpr-dsar/45-01-PLAN.md
@.paul/phases/45-gdpr-dsar/45-01-SUMMARY.md
@.paul/phases/45-gdpr-dsar/45-01-IMPLEMENTATION_NOTES.md

## Source Files (what we're fixing)
@backend/02_features/03_iam/sub_features/08_dsar/repository.py
@backend/02_features/03_iam/sub_features/08_dsar/service.py
@backend/02_features/03_iam/sub_features/08_dsar/routes.py
@backend/02_features/03_iam/sub_features/08_dsar/schemas.py
@backend/09_sql_migrations/20260421_071_dsar.sql
@tests/test_iam_dsar.py

## Ground Truth for IAM Schema
@03_docs/features/03_iam/05_sub_features/03_users/00_bootstrap/09_sql_migrations/01_migrated/20260413_002_iam-users.sql
@backend/02_features/03_iam/sub_features/19_gdpr/service.py
</context>

<acceptance_criteria>

## AC-1: Migration creates exactly what the repository queries

```gherkin
Given the DSAR sub-feature repository queries "03_iam"."65_evt_dsar_jobs" joined to "03_iam"."07_dim_dsar_statuses" and "03_iam"."08_dim_dsar_types"
When the migrator applies 20260421_071_iam-dsar.sql and seeds from the same sub-feature's seeds/ directory
Then those three tables exist with the exact columns repository.py reads/writes (id, org_id, subject_user_id, actor_user_id, actor_session_id, job_type_id, status_id, row_counts, result_location, error_detail, completed_at, created_at, is_test)
And the migration DOWN section cleanly drops all three tables
And the seeds populate dim_dsar_types with rows 'export' and 'delete' and dim_dsar_statuses with 'requested', 'in_progress', 'completed', 'failed'
```

## AC-2: Tests load against the real IAM schema

```gherkin
Given pytest discovers tests/test_iam_dsar.py
When it runs in the project venv against a database with migrations + seeds applied
Then all tests import-load without signature errors
And fixtures successfully INSERT into "03_iam"."12_fct_users" using (id, account_type_id, created_by, updated_by) and populate email via dtl_user_attrs
And all repository calls use keyword arguments matching repository.py's kwarg-only signatures
And at minimum these tests pass: create_dsar_job for export + delete, get_dsar_job, list_dsar_jobs, update_dsar_job_status, delete_user_data idempotency
```

## AC-3: Worker loop is invoked by the running backend

```gherkin
Given backend/main.py is the FastAPI app entry
When the app starts up
Then the lifespan hook launches an asyncio background task that polls run_pending_dsar_exports(pool) and run_pending_dsar_deletes(pool) every 60 seconds
And the task is cancelled cleanly on shutdown
And a fresh DSAR export job inserted with status='requested' transitions through 'in_progress' and terminates at 'completed' (with row_counts populated) or 'failed' (with error_detail) without manual intervention
```

</acceptance_criteria>

<tasks>

<task type="auto">
  <name>Task 1: Rewrite the DSAR migration in per-sub-feature location with numbered tables + dim seeds</name>
  <files>
    03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/02_in_progress/20260421_071_iam-dsar.sql,
    03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/seeds/03iam_dsar_types.yaml,
    03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/seeds/03iam_dsar_statuses.yaml,
    backend/09_sql_migrations/20260421_071_dsar.sql
  </action>
    Delete the monolithic `backend/09_sql_migrations/20260421_071_dsar.sql`. It creates the wrong table names, references `fct_users(user_id)` (column doesn't exist — it's `id`), and seeds into a dim table it never creates.

    Create the replacement at the IAM sub-feature path following per-sub-feature migration convention (Phase 3 Plan 03 decision). File: `03_docs/features/03_iam/05_sub_features/08_dsar/00_bootstrap/09_sql_migrations/02_in_progress/20260421_071_iam-dsar.sql`.

    The migration has standard `-- UP ====` and `-- DOWN ====` sections and creates exactly what `repository.py` already queries:

    1. `"03_iam"."07_dim_dsar_statuses"` — SMALLINT PK (statically seeded via YAML, so plain SMALLINT not IDENTITY per the dim-PK decision in Phase 10 Plan 01). Columns: `id SMALLINT PK`, `code TEXT UNIQUE NOT NULL`, `label TEXT NOT NULL`, `description TEXT`, `deprecated_at TIMESTAMP`.

    2. `"03_iam"."08_dim_dsar_types"` — same shape, same rationale.

    3. `"03_iam"."65_evt_dsar_jobs"` — append-only event. Columns:
       - `id VARCHAR(36) PRIMARY KEY` (UUID v7, populated by app via `_core_id.uuid7()`)
       - `org_id VARCHAR(36) NOT NULL` FK → `"03_iam"."10_fct_orgs"(id)`
       - `subject_user_id VARCHAR(36) NOT NULL` FK → `"03_iam"."12_fct_users"(id)`
       - `actor_user_id VARCHAR(36) NOT NULL` FK → `"03_iam"."12_fct_users"(id)`
       - `actor_session_id VARCHAR(36)` (nullable — not all callers have a session)
       - `job_type_id SMALLINT NOT NULL` FK → `"03_iam"."08_dim_dsar_types"(id)`
       - `status_id SMALLINT NOT NULL` FK → `"03_iam"."07_dim_dsar_statuses"(id)`
       - `row_counts JSONB`
       - `result_location TEXT`
       - `error_detail TEXT`
       - `completed_at TIMESTAMP`
       - `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
       - `is_test BOOLEAN NOT NULL DEFAULT false`
       - No `updated_at` (evt_* rule)
       - No `deleted_at` (evt_* rule)
       - No `created_by` / `updated_by` — instrumentation-emitted rows, per the Phase 13 Plan 01 precedent for evt_* tables with no human actor
    4. Indexes: `(org_id)`, `(subject_user_id)`, `(status_id)`, `(created_at DESC)`.
    5. All constraints explicitly named (`pk_iam_evt_dsar_jobs`, `fk_iam_evt_dsar_jobs_org`, `idx_iam_evt_dsar_jobs_org_id`, etc. per project naming rule).
    6. `COMMENT ON TABLE` and `COMMENT ON COLUMN` for every new object.

    The DOWN section drops all three tables in dependency order (`65_evt_dsar_jobs` first).

    Create the two seed YAML files at the same sub-feature's `seeds/` directory. Use project-convention filename prefix `03iam_*` per the Phase 7 Plan 01 "seed filenames must be globally unique" decision.

    `03iam_dsar_types.yaml`:
    ```
    schema: "03_iam"
    table: "08_dim_dsar_types"
    rows:
      - id: 1
        code: export
        label: Export
        description: Subject Access Request — export user data
        deprecated_at: null
      - id: 2
        code: delete
        label: Delete
        description: Right to be Forgotten — erase user data
        deprecated_at: null
    ```

    `03iam_dsar_statuses.yaml`:
    ```
    schema: "03_iam"
    table: "07_dim_dsar_statuses"
    rows:
      - id: 1
        code: requested
        label: Requested
        description: Job created, waiting for worker
        deprecated_at: null
      - id: 2
        code: in_progress
        label: In Progress
        description: Worker picked up the job
        deprecated_at: null
      - id: 3
        code: completed
        label: Completed
        description: Job finished successfully
        deprecated_at: null
      - id: 4
        code: failed
        label: Failed
        description: Job finished with error; see error_detail
        deprecated_at: null
    ```

    Do not touch `backend/09_sql_migrations/20260421_072_audit_retention_policy.sql` — that is bonus scope; its fate is a separate-plan decision.
  <verify>
    1. `python -m backend.01_migrator.runner status` lists the new migration under 08_dsar.
    2. `python -m backend.01_migrator.runner up` applies it cleanly with no errors.
    3. `python -m backend.01_migrator.runner seed` populates both dim tables (4 rows + 2 rows).
    4. `psql -c '\d "03_iam"."65_evt_dsar_jobs"'` shows the exact column set the repository reads.
    5. `psql -c '\d "03_iam"."07_dim_dsar_statuses"'` and `\d "03_iam"."08_dim_dsar_types"` both exist with the expected rows.
    6. `python -m backend.01_migrator.runner down` reverses cleanly.
  </verify>
  <done>AC-1 satisfied: migration + seeds land three tables matching the repository's SQL exactly; DOWN reverses cleanly.</done>
</task>

<task type="auto">
  <name>Task 2: Rewrite test_iam_dsar.py fixtures + calls against the real IAM schema</name>
  <files>tests/test_iam_dsar.py</files>
  <action>
    Rewrite the existing test file so it actually runs. Current problems:
    - Fixture inserts `fct_users (user_id, email, created_by)` — columns don't exist (real columns: `id`, `account_type_id`, `is_active`, `is_test`, `deleted_at`, `created_by`, `updated_by`, created_at/updated_at); email lives in `dtl_user_attrs` (EAV).
    - Fixture inserts `fct_orgs (org_id, org_name)` — unprefixed column names; actual table is `"03_iam"."10_fct_orgs"` with `id`, `account_type_id`-style schema.
    - Test calls `_dsar_repo.create_dsar_job(conn, actor, subject, org, "export")` — positional, but repo signature is keyword-only with kwargs `(conn, *, job_id, org_id, subject_user_id, actor_user_id, job_type, actor_session_id=None)`.

    Fix approach:

    1. Create a `dsar_fixtures` fixture that:
       - Inserts one org into `"03_iam"."10_fct_orgs"` using the actual column set (check the ground-truth migration for 10_fct_orgs — follow the same pattern as `tests/conftest.py` if a helper already exists).
       - Inserts two users (one actor, one subject) into `"03_iam"."12_fct_users"` with columns `(id, account_type_id, is_test, created_by, updated_by)`; account_type_id = 1 (email_password seed) or whatever exists.
       - Populates email for the subject via `dtl_user_attrs` (using `dim_attr_defs.code = 'email'`) — this mirrors the EAV pattern, but only if any DSAR test actually asserts on email. If no test needs email, skip EAV.
       - Yields `{org_id, actor_user_id, subject_user_id}` dict.
       - Teardown: DELETE rows (in FK-safe order) in a finalizer.

    2. Replace every `_dsar_repo.create_dsar_job(conn, test_actor_id, test_user_id, test_org_id, "export")` with the keyword form:
       ```python
       job_id = _id.uuid7()
       await _dsar_repo.create_dsar_job(
           conn,
           job_id=job_id,
           org_id=fixtures["org_id"],
           subject_user_id=fixtures["subject_user_id"],
           actor_user_id=fixtures["actor_user_id"],
           actor_session_id=None,
           job_type="export",
       )
       ```
       And fetch the row via `get_dsar_job(conn, job_id)`.

    3. Keep the two schema unit tests (`test_dsar_export_request_schema`, `test_dsar_delete_request_schema`) as-is — they don't touch the DB.

    4. Drop `test_delete_soft_deletes_user` if `delete_user_data` is gated on rows that existing fixtures don't provide cleanly; leave a TODO referencing 45-01c for the full cascade test. Do NOT leave broken tests in the file.

    5. Verify `NodeContext` is importable from `backend.01_catalog.context` and carries `workspace_id` — the old tests reference `_ctx_mod` with `workspace_id` keyword; match the real NodeContext signature (check `backend/01_catalog/context.py` if uncertain).

    Avoid: writing new helpers in `backend/` to "help" tests (that's scope creep — tests should use the existing repo surface). Avoid: mocking the DB — DSAR is all SQL, mocks would be meaningless.
  </action>
  <verify>
    1. `.venv/bin/pytest tests/test_iam_dsar.py --collect-only` lists every test without ImportError or TypeError.
    2. `.venv/bin/pytest tests/test_iam_dsar.py -v` passes every test against a local DB that has 45-01b's migration applied.
    3. No test references `org_name` or `email` as a direct fct column.
    4. `grep -n "create_dsar_job" tests/test_iam_dsar.py` shows only keyword-argument calls.
  </verify>
  <done>AC-2 satisfied: tests import-load and run against the real IAM schema with all keyword-only repo signatures respected.</done>
</task>

<task type="auto">
  <name>Task 3: Wire the DSAR worker loop into backend/main.py lifespan</name>
  <files>backend/main.py</files>
  <action>
    The service module already exports `run_pending_dsar_exports(pool)` and `run_pending_dsar_deletes(pool)` (they `asyncio.create_task(...)` per-job workers). Nothing calls them — jobs sit at `status='requested'` forever.

    Find the existing lifespan / startup hook in `backend/main.py`. Look for either:
    - An existing GDPR worker task (`gdpr_worker_loop` from `19_gdpr/service.py`) — if present, add DSAR polls to it OR add a sibling task.
    - A FastAPI `@asynccontextmanager async def lifespan(app)` block — add a background task there.

    Preferred implementation (self-contained DSAR worker, matches existing GDPR pattern):
    ```python
    # inside lifespan, after pool is initialized:
    _iam_dsar_svc = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")

    async def _dsar_worker_loop(pool):
        logger = logging.getLogger("tennetctl.iam.dsar.worker")
        while True:
            try:
                await _iam_dsar_svc.run_pending_dsar_exports(pool)
            except Exception:
                logger.exception("DSAR export worker tick failed")
            try:
                await _iam_dsar_svc.run_pending_dsar_deletes(pool)
            except Exception:
                logger.exception("DSAR delete worker tick failed")
            await asyncio.sleep(60)

    dsar_task = asyncio.create_task(_dsar_worker_loop(app.state.pool))
    try:
        yield
    finally:
        dsar_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await dsar_task
    ```

    If `backend/main.py` already has a worker registry / list pattern, use it instead of adding a bespoke task — the goal is one worker-loop style in the app, not two.

    Do NOT touch vault integration in `_process_dsar_export_job` — the "store export JSON" TODO is intentional scope-out of this plan. A job will still transition `requested → in_progress → completed` with `result_location` set to the stub path; real vault persistence is 45-01c.

    Avoid: adding a new dependency, introducing a threading model, adding retry with exponential backoff (the existing per-task `_process_dsar_export_job` already catches exceptions and marks failed), changing the 60-second poll cadence without cause.
  </action>
  <verify>
    1. `.venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0` starts cleanly; logs show the DSAR worker loop began.
    2. Send `POST /v1/dsar/export-request` with a seeded user/org; log shows `run_pending_dsar_exports` picked up a row within 60s.
    3. Poll `GET /v1/dsar/jobs/{id}` — status transitions `requested → in_progress → completed` and `result_location` is populated (stub path is fine for this plan).
    4. Ctrl-C shuts down cleanly with no `Task was destroyed but it is pending!` warnings.
    5. `grep -n "dsar" backend/main.py` shows the worker is registered.
  </verify>
  <done>AC-3 satisfied: worker is invoked from lifespan; jobs transition end-to-end; shutdown is clean.</done>
</task>

</tasks>

<boundaries>

## DO NOT CHANGE
- `backend/02_features/03_iam/sub_features/08_dsar/schemas.py` — schema shapes are correct; only tests + migration + main.py need changes.
- `backend/02_features/03_iam/sub_features/08_dsar/repository.py` — the repo is the ground-truth design we're aligning to.
- `backend/02_features/03_iam/sub_features/08_dsar/service.py` — keep as-is for this plan; the inline `_emit_audit` SQL insert is a known scope-out (see 45-01c).
- `backend/02_features/03_iam/sub_features/08_dsar/routes.py` — already registered; no changes needed.
- `backend/02_features/03_iam/sub_features/29_authz_gates/authz_helpers.py` — bonus scope; triage decision is a separate plan.
- `backend/02_features/04_audit/sub_features/02_retention/**` — bonus scope; retro-plan or revert is a separate plan.
- `backend/09_sql_migrations/20260421_072_audit_retention_policy.sql` — same, bonus scope.
- Every migration file deleted in commit `482c981` — do not attempt to restore. First verify whether the listed monitoring + IAM migrations (071–080, 053, 043) were already applied before rescue action.

## SCOPE LIMITS
- Vault storage of the export JSON stays a TODO in `_process_dsar_export_job`. Real vault integration is **Plan 45-01c**.
- Audit emission stays via inline raw SQL in `_emit_audit`. Moving to `run_node("audit.events.emit")` is **Plan 45-01c**.
- Signed download URL generation stays as `result["download_url"] = result["result_location"]`. Real signing is **Plan 45-01c**.
- Event key names (`iam.dsar.export_requested` / `iam.dsar.delete_requested`) stay as-is. Renaming to `.exported` / `.deleted` belongs to the audit-rework plan.
- Manifest registration of the 08_dsar sub-feature and its nodes belongs to **Plan 45-01c**.
- Bonus-scope triage (audit retention + authz_helpers) is not touched here — separate plan decisions.
- No new sub-features. No new dependencies. No changes to Phase 38 rate limiter or audit retention.

</boundaries>

<verification>
Before declaring plan complete:
- [ ] Migration runs UP + DOWN cleanly on a fresh database; seeds populate.
- [ ] `.venv/bin/pytest tests/test_iam_dsar.py -v` all tests pass.
- [ ] `.venv/bin/python -c "from backend.02_features.03_iam.sub_features.08_dsar import repository, service, routes, schemas"` completes silently (import sanity).
- [ ] Backend boots with `uvicorn backend.main:app --port 51734` and logs the DSAR worker loop started.
- [ ] Manual curl of `POST /v1/dsar/export-request` followed by polling `GET /v1/dsar/jobs/{id}` shows `requested → in_progress → completed` without manual intervention.
- [ ] `pyright backend/02_features/03_iam/sub_features/08_dsar/ tests/test_iam_dsar.py backend/main.py` exits 0.
- [ ] All three acceptance criteria satisfied.
</verification>

<success_criteria>
- Migration + repo + tests all reference the same three tables with the same columns.
- Plan 45-01's code artifacts become runnable — no import errors, no signature mismatches, no missing tables.
- DSAR worker transitions jobs end-to-end on a running stack.
- No drift introduced into the bonus-scope or out-of-plan files.
- Uncommitted working-tree state from prior sessions is not further disturbed.
</success_criteria>

<output>
After completion, create `.paul/phases/45-gdpr-dsar/45-01b-SUMMARY.md` following the standard SUMMARY template:
- AC pass/fail table
- Files created/modified
- Decisions (expect at least one re: dim-table design vs. TEXT-CHECK)
- Confirm-or-deny status of commit 482c981's deleted monitoring migrations (mandatory finding)
- Next-phase readiness pointing at 45-01c (real vault + audit via run_node + manifest registration + bonus-scope triage)
</output>
