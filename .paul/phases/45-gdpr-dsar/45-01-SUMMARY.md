---
phase: 45-gdpr-dsar
plan: 45-01
subsystem: iam
tags: [dsar, gdpr, compliance, audit, operator-tooling]

requires:
  - phase: 03-iam-audit
    provides: fct_users, fct_orgs, audit emission path
  - phase: 07-vault
    provides: vault client (planned storage target for export JSON)

provides:
  - iam.dsar sub-feature (schemas + repository + service + routes)
  - POST /v1/dsar/export-request, POST /v1/dsar/delete-request, GET /v1/dsar/jobs, GET /v1/dsar/jobs/{id}
  - Migration 071 (evt_dsar_jobs table — text-enum variant, NOT connected to repository)
  - Bonus: audit.retention sub-feature + migration 072 (out-of-plan scope creep)
  - Bonus: iam.authz_gates authz_helpers.py (out-of-plan scope creep)

affects: [46-admin-ui-dsar, 45-02-self-service-portal, v0.8.0-milestone-gate]

tech-stack:
  added: []
  patterns:
    - "Operator-triggered DSAR via POST request bodies (not implicit from auth context)"
    - "Polling worker loop pattern (asyncio.create_task dispatch from service module)"

key-files:
  created:
    - backend/02_features/03_iam/sub_features/08_dsar/schemas.py
    - backend/02_features/03_iam/sub_features/08_dsar/repository.py
    - backend/02_features/03_iam/sub_features/08_dsar/service.py
    - backend/02_features/03_iam/sub_features/08_dsar/routes.py
    - backend/09_sql_migrations/20260421_071_dsar.sql
    - tests/test_iam_dsar.py
    - backend/02_features/04_audit/sub_features/02_retention/*.py (bonus scope)
    - backend/09_sql_migrations/20260421_072_audit_retention_policy.sql (bonus scope)
    - backend/02_features/03_iam/sub_features/29_authz_gates/authz_helpers.py (bonus scope)
  modified:
    - backend/02_features/03_iam/routes.py (router include only)

key-decisions:
  - "No NATS for async jobs — use existing polling worker pattern (IMPLEMENTATION_NOTES §1)"
  - "Rate-limit via SQL COUNT, not core.rate_limit.check node (that node does not exist)"
  - "evt_dsar_jobs immutable (status transitions, no updated_at)"
  - "Skip iam.dsar.exported / iam.dsar.deleted effect nodes; emit audit inline via direct SQL INSERT"

patterns-established:
  - "None durable — this plan shipped with structural drift; do not copy patterns until rework lands"

duration: ~unknown (code committed 2026-04-21, never verified)
started: 2026-04-21
completed: 2026-04-21 (code-commit only — NOT production-viable)
---

# Phase 45 Plan 01: GDPR DSAR Backend Summary

**Sub-feature scaffolded and committed, but migration ↔ repository ↔ tests are structurally mismatched. APPLY is not production-viable and must be reworked before 45-01 can gate v0.8.0.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | Code written over 6 commits (a1fa4a0 → a4604ec) |
| Files created | 9 (6 in-scope, 3 bonus) |
| Files modified | 1 (IAM router include) |
| Tests | 8 declared (6 async + 2 sync); none verified to pass |
| Net LOC | ~1,960 backend + 212 tests + 66 SQL |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: `POST /v1/dsar/export-request` creates async job | 🟡 Partial | Route exists; repository INSERT references non-existent dim tables — will raise at runtime |
| AC-2: `GET /v1/dsar/jobs/{id}` polls status + download URL | 🟡 Partial | Route + service exist; `download_url` is a pass-through of `result_location`, not a signed URL |
| AC-3: Export includes user + orgs + workspaces + sessions + audit + subs | 🔴 Fail | `repo.export_user_data` scaffolded but not verified; data aggregation untested |
| AC-4: Export format JSON Lines | 🔴 Fail | `DsarExportData` schema produces a single object, not JSONL; nothing written to vault |
| AC-5: `POST /v1/dsar/delete-request` hard-deletes atomically | 🔴 Fail | `_process_dsar_delete_job` uses `async with pool.acquire()` but no explicit `conn.transaction()` — not atomic |
| AC-6: Delete is idempotent | 🟡 Partial | Logic appears idempotent (checks `deleted_at`); test asserts `>= 0` (weak) |
| AC-7: Audit events emitted (`iam.dsar.exported` / `iam.dsar.deleted`) | 🔴 Fail | `_emit_audit` writes directly to `04_audit.60_evt_audit_events` via raw SQL (not via `run_node` / `audit.events.emit`); also emitting `.export_requested` / `.delete_requested` keys, not `.exported` / `.deleted` as plan specified |
| AC-8: Rate limiting 10/hr/workspace | 🟡 Partial | `repo.check_rate_limit` exists; scoped to `org_id` not `workspace_id` as plan specified; no test |
| AC-9: All data removed from Postgres | 🔴 Fail | `repo.delete_user_data` exists but not wired through worker atomically; `evt_audit` rows where `actor_id = X` are not enumerated |
| AC-10: pyright exit 0 + pytest green (80%+) | 🔴 Fail | Not verified. Test fixtures reference column names that don't match actual `fct_users` / `fct_orgs` schema (`user_id` / `org_id` vs `id`) |

**Net:** 0 pass, 4 partial, 6 fail. Plan did not reach "done".

## Accomplishments

- Sub-feature **directory structure + 5-file layout** in place (`08_dsar/`)
- Routes wired into `03_iam/routes.py` via `router.include_router`
- Service-level **polling worker skeleton** (`run_pending_dsar_exports` / `run_pending_dsar_deletes`)
- Commit provenance preserved across 6 atomic commits (easy to revert or rebase)

## Task Commits

| Commit | Type | Description |
|--------|------|-------------|
| `a1fa4a0` | feat | Initial 08_dsar sub-feature (schemas + repo + service + routes) + migration 081 + tests |
| `742aa83` | fix  | Manifest validation fixes (emits_audit on effect nodes; drop `workers` blocks) |
| `2f69e67` | fix  | Phase 40-44 stub handlers to NCP v1 Node classes (unrelated carry) |
| `482c981` | feat | Register DSAR routes in IAM router + rename 081 → 071 (and clean up stale monitoring migrations — potentially destructive!) |
| `0cfa398` | feat | Re-add migration 081 for DSAR job tracking (duplicate / confused history) |
| `a4604ec` | feat | Migration renamed to 071; schema changed to TEXT enum (breaking repo); + bonus scope (audit retention + authz helpers) |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/02_features/03_iam/sub_features/08_dsar/schemas.py` | Created (54 ln) | DsarExportRequest/DeleteRequest/JobResponse + enums |
| `backend/02_features/03_iam/sub_features/08_dsar/repository.py` | Created (289 ln) | Raw SQL against `65_evt_dsar_jobs` + `07_dim_dsar_statuses` + `08_dim_dsar_types` (none of which exist in migration 071) |
| `backend/02_features/03_iam/sub_features/08_dsar/service.py` | Created (392 ln) | create_export_request, create_delete_request, poll_dsar_job, list_jobs, worker dispatch |
| `backend/02_features/03_iam/sub_features/08_dsar/routes.py` | Created (153 ln) | 4 FastAPI routes with ad-hoc `_Ctx` inline class (not NodeContext) |
| `backend/09_sql_migrations/20260421_071_dsar.sql` | Created (66 ln) | `evt_dsar_jobs` (TEXT enum variant) + `v_dsar_jobs` view + seed INSERT into non-existent `dim_dsar_job_statuses` |
| `tests/test_iam_dsar.py` | Created (212 ln) | 8 tests using positional args that don't match repo's keyword-only signatures |
| `backend/02_features/03_iam/routes.py` | Modified | Add `router.include_router(_dsar_routes.router)` |
| — | — | **Bonus / out-of-plan:** |
| `backend/02_features/04_audit/sub_features/02_retention/` | Created | Full audit retention sub-feature (schemas/service/routes) |
| `backend/09_sql_migrations/20260421_072_audit_retention_policy.sql` | Created | Retention policy migration |
| `backend/02_features/03_iam/sub_features/29_authz_gates/authz_helpers.py` | Created (182 ln) | Authz helper utilities |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| No NATS; extend polling worker | Existing `19_gdpr` module uses the same pattern | Consistency with GDPR sub-feature; 60s lag acceptable |
| SQL-based rate limit | `core.rate_limit.check` node does not exist | Works without new platform node; diverges from Phase 38's PG-native limiter |
| Skip `iam.dsar.exported` / `iam.dsar.deleted` effect nodes | Rushed apply; audit emitted inline | **Violates** project rule "effects must emit audit via triple-defense + `run_node`"; registered in Decisions 251 but ignored here |
| Schema shape swapped mid-apply | Commit `a4604ec` replaced IDENTITY+dim design with TEXT-CHECK variant | Left repository (originally written against dim design) pointing at tables that were never created |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 0 | — |
| Scope additions (out-of-plan shipped) | 3 | Audit retention sub-feature + migration 072 + authz_helpers — large, unreviewed |
| Deferred / dropped from plan | 5 | See below |
| Structural drift (code does not match itself) | 3 | Migration ↔ repo ↔ tests are three different designs |

**Total impact:** Plan 45-01 is **not production-viable as shipped**. Requires rework before v0.8.0 can gate on DSAR.

### Structural Drift (CRITICAL — must be resolved)

**1. Migration shape ≠ Repository shape**
- Migration 071 creates `03_iam.evt_dsar_jobs` with columns `(job_id, job_type TEXT CHECK, status TEXT CHECK)`
- Repository queries `"03_iam"."65_evt_dsar_jobs"` (prefixed table name) with columns `(id, job_type_id, status_id)` joined against `07_dim_dsar_statuses` / `08_dim_dsar_types`
- Neither dim table is created by any migration; the migration seeds `dim_dsar_job_statuses` (different name) — **SEED WILL FAIL** on apply

**2. Test fixtures ≠ actual IAM schema**
- Fixtures `INSERT INTO 03_iam.fct_orgs (org_id, org_name)` and `fct_users (user_id, email, created_by)`
- Actual IAM tables use `id` / `name` (unprefixed) columns per convention
- Tests cannot run against current DB schema

**3. Test calls ≠ repository signature**
- Tests call `_dsar_repo.create_dsar_job(conn, test_actor_id, test_user_id, test_org_id, "export")` — positional
- Repository signature is keyword-only: `create_dsar_job(conn, *, job_id, org_id, subject_user_id, actor_user_id, job_type, actor_session_id=None)`
- Tests cannot import-load without erroring

### Plan Items Dropped

| Dropped | Plan reference | Reason |
|---------|---------------|--------|
| `iam.dsar.exported` effect node | Plan §Audit Emission | Skipped; audit emitted via raw SQL INSERT instead |
| `iam.dsar.deleted` effect node | Plan §Audit Emission | Same as above |
| Manifest registration of 08_dsar | Plan §Files to Modify | `feature.manifest.yaml` has no dsar entry |
| Register in `backend/main.py` | Plan §Files to Modify | Only added to `03_iam/routes.py`; worker loop NEVER wired into `main.py` startup (jobs will stay in `requested` forever) |
| Vault storage of export JSON | Plan §Export Data Model, §Vault Integration | Stubbed; `_process_dsar_export_job` computes a path but does not call vault client |
| Signed download URL | Plan AC-2 | `result["download_url"] = result["result_location"]` — no signing |

### Bonus Scope (out-of-plan, shipped anyway)

| Addition | Files | Concern |
|----------|-------|---------|
| Audit retention sub-feature | `04_audit/02_retention/` (schemas.py + service.py + routes.py, 402 lines) | Separate phase (no plan, no AC, no review) shipped as a commit-along |
| Migration 072 audit_retention_policy | `20260421_072_audit_retention_policy.sql` (87 lines) | Schema change outside plan boundary |
| authz_helpers | `29_authz_gates/authz_helpers.py` (182 lines) | Related to "AUTHZ-GATES-REMEDIATION" in `.paul/` root but no plan |

These should either get retroactive PLANs or be reverted.

### Commit `482c981` Potentially Destructive

In the same commit that registered the DSAR router, this file list was **deleted**:
- `20260420_071_monitoring-escalation-policies.sql` (152 ln)
- `20260420_072_monitoring-oncall-schedules.sql` (151 ln)
- `20260420_073_monitoring-action-templates.sql` (117 ln)
- `20260420_074_monitoring-action-deliveries.sql` (76 ln)
- `20260420_075_monitoring-incidents.sql` (172 ln)
- `20260420_076_monitoring-incident-grouping.sql` (52 ln)
- `20260420_077_monitoring-slo.sql` (199 ln)
- `20260420_078_monitoring-slo-budget.sql` (96 ln)
- `20260420_079_monitoring-dashboard-sharing.sql` (171 ln)
- `20260420_080_monitoring-dashboard-share-events.sql` (102 ln)
- `20260417_053_add-last-activity-at.sql` (22 ln)
- `20260418_043_iam-impersonation.sql` (35 ln)

These were in `02_in_progress/`. If the migrator had already applied them and moved them to `01_migrated/` then deletion is fine. If not, **Phase 39-41 monitoring migrations are lost**. Verify before the next `/paul:apply`.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| 51 uncommitted files in working tree pre-dating plan | Not addressed by this plan; `project_audit_handoff_2026_04_20.md` memory documents this as a known issue |
| Repo-to-migration drift | Discovered at UNIFY time; not resolved |

## Next Phase Readiness

**Ready:**
- Nothing durable. Do not build on Plan 45-01 output until rework lands.

**Concerns:**
- v0.8.0 milestone gate is on **DSAR operator compliance** (this plan). v0.8.0 cannot ship until 45-01 is reworked.
- Phase 45-02 (self-service portal, deferred v1.0) should **not** be planned against current 45-01 APIs — those APIs will move when the drift is fixed.
- Bonus scope (audit retention, authz helpers) is unplanned and unreviewed — should be either retroactive-planned or reverted.

**Blockers:**
- Migration 071 seed (`dim_dsar_job_statuses`) will fail on apply (table doesn't exist).
- Repository will raise `relation "03_iam"."65_evt_dsar_jobs" does not exist` on first call.
- Worker loop is not invoked anywhere; jobs will stall at `requested`.

**Recommended next action:** `/paul:plan 45-01-REWORK` — a fix-forward plan that:
1. Picks ONE of the two schema designs (TEXT-CHECK or IDENTITY-with-dim) and aligns migration + repo + tests.
2. Wires `run_pending_dsar_exports` / `run_pending_dsar_deletes` into `backend/main.py` startup hooks alongside the existing GDPR worker.
3. Wires vault client into `_process_dsar_export_job` for actual JSON storage + signed-URL retrieval.
4. Replaces inline `_emit_audit` with `run_node("audit.events.emit", ...)` or registers `iam.dsar.exported` / `iam.dsar.deleted` effect nodes and wires them through the runner.
5. Decides fate of bonus-scope audit retention + authz_helpers (retro-plan or revert).
6. Verifies AC-1 through AC-10 with pytest + Playwright MCP on a running stack.

---
*Phase: 45-gdpr-dsar, Plan: 45-01*
*Completed (code-commit only): 2026-04-21*
*Status: APPLIED-BUT-BROKEN — rework required before v0.8.0 can ship*
