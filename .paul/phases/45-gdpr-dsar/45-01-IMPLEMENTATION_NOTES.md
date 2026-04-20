# Phase 45-01 Implementation Notes — GDPR DSAR Backend

**Date:** 2026-04-20  
**Analyst:** Claude Code  
**Status:** READY FOR IMPLEMENTATION

---

## Executive Summary

Phase 45-01 extends the existing `19_gdpr` sub-feature (Art 15/17 self-service) with operator-triggered DSAR compliance audits (`08_dsar`). Both systems coexist in the same IAM feature with separate routes and tables:
- **Existing:** `/v1/account/*` (user self-service) + `10_fct_gdpr_jobs` table
- **New:** `/v1/dsar/*` (operator bulk audits) + `evt_dsar_jobs` table

Implementation is **straightforward but requires precision** on:
1. Migration 071 (table + views + dims)
2. Async job handling (background loop pattern, not NATS—see findings)
3. Audit scope enforcement (mandatory user_id + session_id + org_id + workspace_id)
4. Delete cascade idempotency (check deleted_at before each operation)

---

## Key Findings from Code Analysis

### 1. NATS Not Used in IAM Module

Initial plan assumed NATS/JetStream for async jobs. **Reality check:**
- `backend/01_core/nats.py` exists and is configured, but **no sub-feature in IAM currently uses it**
- Existing GDPR module uses **background worker loop** (`async def gdpr_worker_loop(pool) → while True: ...`)
- Pattern: service layer has `run_pending_exports/run_pending_erasures` functions, called by background task in `backend/main.py`
- **Decision:** Extend existing worker loop in `19_gdpr/service.py` to also handle DSAR jobs. No NATS needed for v0.8.0.

### 2. Audit Scope Mandatory (From CLAUDE.md feedback)

Every audit event in this project must carry:
```python
{
  "user_id": "...",      # actor performing the action
  "session_id": "...",   # session context
  "org_id": "...",       # org scope
  "workspace_id": "..."  # workspace scope
}
```

**Two exceptions (bypass via `audit_category="setup"`):**
1. Setup operations (auth, bootstrap)
2. Failure outcomes (when actor is being established)

**For DSAR:** Operator triggers export/delete → carries operator's user_id + session_id, not subject's. This is audit-of-action, not audit-by-user.

### 3. Existing GDPR Module Structure

**Key patterns to mirror:**

**schemas.py:** Minimal models; separate IN/OUT models
```python
class ExportRequestIn(BaseModel):
    pass  # No body — auth context carries user_id

class GdprJobOut(BaseModel):
    id: str
    user_id: str
    kind: str
    status: str
    # ... timestamps, etc.
```

**repository.py:** Raw SQL + dim lookups
```python
async def _kind_id(conn, code: str) -> int:
    row = await conn.fetchrow(f"SELECT id FROM {_KINDS} WHERE code = $1", code)
    if row is None:
        raise RuntimeError(f"gdpr kind not found: {code}")
    return int(row["id"])
```

**service.py:** Business logic + audit emission via `_catalog.run_node(pool, "audit.events.emit", ctx, {...})`
```python
async def _emit_audit(pool, ctx, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata}
    )
```

**routes.py:** Context building (with audit_category), pool/conn lifecycle, error handling
```python
def _build_ctx(request: Request, pool: Any) -> Any:
    return NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        audit_category="user",  # or "setup" for bootstrap
        pool=pool,
        extras={"pool": pool},
    )
```

### 4. Rate Limiting Pattern

From `auth_policy.py`: Rate limits stored as **auth policy config**, not in code.
- Not using node-based rate limiting (PLAN mentioned `core.rate_limit.check`, but that node may not exist yet)
- **For v0.8.0:** Simple in-memory approach or skip (defer to v0.9)
- **Alternative:** Implement a simple PG-native rate_limit check: `SELECT COUNT(*) FROM evt_dsar_jobs WHERE org_id = $1 AND created_at > NOW() - INTERVAL '1 hour'`

---

## Implementation Sequence

### Step 1: Migration 071 (evt_dsar_jobs table + dims)

**File:** `03_docs/features/03_iam/05_sub_features/08_dsar/09_sql_migrations/02_in_progress/20260421_071_dsar-jobs.sql`

Key table design:
- **evt_dsar_jobs** (immutable, append-only)
  - `job_id UUID v7 PRIMARY KEY`
  - `job_type` (export | delete) — NOT a FK to dim (enum-like)
  - `actor_user_id UUID v7` (operator who triggered)
  - `subject_user_id UUID v7` (whose data)
  - `org_id UUID v7` (org scope)
  - `workspace_id UUID v7` (workspace scope)
  - `status` (requested | in_progress | completed | failed) — TEXT enum
  - `row_counts JSONB` — `{"users": 1, "orgs": 3, "audit_events": 127, ...}`
  - `error_message TEXT`
  - `result_location TEXT` — vault key `iam.dsar.export.{job_id}`
  - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - `completed_at TIMESTAMP`
  - `created_by VARCHAR(36)` (system/operator user_id)
  - `is_test BOOLEAN DEFAULT false`
  - **NO** updated_at, NO soft-delete (immutable)

- Indexes:
  - `(org_id)` — list jobs by org
  - `(subject_user_id)` — fetch all DSAR events for a user (data subject rights)
  - `(status)` WHERE status != 'completed' — find in-progress jobs
  - `(created_at)` DESC — list recent jobs

- **No separate dim tables** (unlike GDPR's dim_gdpr_kinds/statuses). Status is TEXT enum for simplicity.

- **View:** `v_dsar_jobs` (resolve actor_user_id to display_name, status, counts, timestamps)

### Step 2: Create Backend Sub-Feature `08_dsar`

**Directory:** `backend/02_features/03_iam/sub_features/08_dsar/`

**Files:**
1. `__init__.py` (empty)
2. `schemas.py` (3 Pydantic models)
3. `repository.py` (5–7 functions)
4. `service.py` (5 async functions + worker loop additions)
5. `routes.py` (4 endpoints)

### Step 3: Extend Existing GDPR Worker Loop

**File:** `backend/02_features/03_iam/sub_features/19_gdpr/service.py`

Add:
```python
async def run_pending_dsar_exports(pool: Any) -> None:
    """Pick up requested DSAR export jobs and process them."""
    # Query evt_dsar_jobs where status='requested' and job_type='export'
    # Call _process_dsar_export_job for each

async def run_pending_dsar_deletes(pool: Any) -> None:
    """Pick up requested DSAR delete jobs and process them."""
    # Query evt_dsar_jobs where status='requested' and job_type='delete'
    # Call _process_dsar_delete_job for each

async def gdpr_worker_loop(pool: Any) -> None:
    """Background asyncio task — polls every 60 seconds."""
    while True:
        try:
            await run_pending_exports(pool)      # existing
        except Exception:
            logger.exception("GDPR export worker error")
        try:
            await run_pending_erasures(pool)     # existing
        except Exception:
            logger.exception("GDPR erasure worker error")
        try:
            await run_pending_dsar_exports(pool) # NEW
        except Exception:
            logger.exception("DSAR export worker error")
        try:
            await run_pending_dsar_deletes(pool) # NEW
        except Exception:
            logger.exception("DSAR delete worker error")
        await asyncio.sleep(60)
```

### Step 4: Code Implementation Details

#### schemas.py

```python
class DsarExportRequest(BaseModel):
    subject_user_id: str
    org_id: str
    # workspace_id comes from auth context

class DsarDeleteRequest(BaseModel):
    subject_user_id: str
    org_id: str
    # workspace_id comes from auth context

class DsarJobResponse(BaseModel):
    job_id: str
    actor_user_id: str
    subject_user_id: str
    org_id: str
    status: Literal["requested", "in_progress", "completed", "failed"]
    job_type: Literal["export", "delete"]
    row_counts: dict | None
    error_message: str | None
    result_location: str | None  # vault key for exports
    created_at: datetime
    completed_at: datetime | None
```

#### repository.py

```python
async def create_dsar_job(
    conn: Any,
    job_id: str,
    actor_user_id: str,
    subject_user_id: str,
    org_id: str,
    workspace_id: str,
    job_type: str,  # "export" | "delete"
    created_by: str,
) -> dict:
    """INSERT evt_dsar_jobs row."""

async def get_dsar_job(conn: Any, job_id: str) -> dict | None:
    """SELECT * FROM v_dsar_jobs WHERE job_id = $1."""

async def list_dsar_jobs(
    conn: Any,
    org_id: str,
    workspace_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List DSAR jobs scoped to org/workspace."""

async def update_dsar_job_status(
    conn: Any,
    job_id: str,
    status: str,
    row_counts: dict | None = None,
    error_message: str | None = None,
    result_location: str | None = None,
) -> None:
    """Update status + optional counts/error/location."""

async def export_user_data(pool: Any, subject_user_id: str, org_id: str) -> dict:
    """Aggregate all user data (orgs, workspaces, sessions, audit events, etc.)
    Return as dict ready for JSON serialization.
    Chunked reads to avoid OOM.
    """

async def delete_user_data(conn: Any, subject_user_id: str, org_id: str) -> dict:
    """Hard-delete all user data in single transaction.
    Return row_counts: {"users": 1, "sessions": 3, "audit_events": 127, ...}
    Idempotent: checks deleted_at before deleting fct_users.
    """

async def user_belongs_to_org(conn: Any, user_id: str, org_id: str) -> bool:
    """Verify user has membership in org (org_scope check)."""
```

#### service.py

```python
async def create_export_request(
    pool: Any, conn: Any, ctx: Any,
    subject_user_id: str, org_id: str
) -> dict:
    """
    1. Check actor has org_id scope (or is admin)
    2. Check subject_user_id belongs to org_id
    3. Rate limit: 10 DSAR ops/org/hour
    4. Create evt_dsar_jobs row with status='requested'
    5. Emit audit: "iam.dsar.export_requested"
    6. Return job_id
    Note: async processing happens in worker loop.
    """

async def create_delete_request(
    pool: Any, conn: Any, ctx: Any,
    subject_user_id: str, org_id: str
) -> dict:
    """Same as export but job_type='delete'."""

async def get_dsar_job(
    pool: Any, conn: Any, ctx: Any,
    job_id: str
) -> dict:
    """
    1. Verify actor has org_id scope
    2. Retrieve job from v_dsar_jobs
    3. If status='completed' + result_location, generate vault download URL (signed)
    4. Return job details + download_url (if ready)
    """

async def list_dsar_jobs(
    pool: Any, conn: Any, ctx: Any,
    org_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List jobs scoped to actor's org (or all if admin)."""

async def _process_dsar_export_job(pool: Any, job_id: str, subject_user_id: str, org_id: str, workspace_id: str) -> None:
    """
    1. Update status → "in_progress"
    2. Call repo.export_user_data(pool, subject_user_id, org_id)
    3. Serialize to JSON, store in vault at key iam.dsar.export.{job_id} (90-day TTL)
    4. Update status → "completed", set result_location
    5. Emit audit: "iam.dsar.exported" with row_counts
    6. If any exception: update status → "failed", error_message
    """

async def _process_dsar_delete_job(pool: Any, job_id: str, subject_user_id: str, org_id: str, workspace_id: str) -> None:
    """
    1. Update status → "in_progress"
    2. Call repo.delete_user_data(conn, subject_user_id, org_id) in a transaction
    3. Capture row_counts returned
    4. Update status → "completed", set row_counts
    5. Emit audit: "iam.dsar.deleted" with row_counts
    6. If any exception: update status → "failed", error_message
    """
```

#### routes.py

```python
@router.post("/export-request", status_code=202)
async def dsar_export_request(
    request: Request,
    body: DsarExportRequest
) -> Any:
    """POST /v1/dsar/export-request"""
    # Context + rate limit check
    # Call service.create_export_request()
    # Return {"ok": True, "data": {"job_id": "..."}}

@router.post("/delete-request", status_code=202)
async def dsar_delete_request(
    request: Request,
    body: DsarDeleteRequest
) -> Any:
    """POST /v1/dsar/delete-request"""

@router.get("/jobs/{job_id}")
async def get_dsar_job(
    request: Request,
    job_id: str
) -> Any:
    """GET /v1/dsar/jobs/{job_id}"""
    # Call service.get_dsar_job()
    # Return {"ok": True, "data": {..., "download_url": "..."}}

@router.get("/jobs")
async def list_dsar_jobs(
    request: Request,
    org_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Any:
    """GET /v1/dsar/jobs?org_id=X&status=completed"""
    # Call service.list_dsar_jobs()
    # Return {"ok": True, "data": [...], "total": 42}
```

---

## Critical Decisions & Rationale

### 1. No NATS — Extend Existing Worker Loop
- **Why:** Existing GDPR module uses simple background task. No need to introduce NATS complexity.
- **Trade-off:** Polling every 60s (not real-time). Acceptable for compliance audits.
- **Benefit:** Simpler deployment, fewer dependencies, easier testing.

### 2. evt_dsar_jobs Is Immutable (NO updated_at)
- **Why:** Event sourcing pattern. Immutable append-only log of DSAR requests.
- **How:** Use STATUS transitions (requested → in_progress → completed), not UPDATE on same row.
- **Trade-off:** To "cancel" a job, insert a new cancel event (not implemented in v0.8.0).

### 3. Rate Limit via SQL Query (Not Node)
- **Why:** `core.rate_limit.check` node may not exist yet in Phase 38.
- **Implementation:** Simple SELECT COUNT(*) ... INTERVAL '1 hour' before INSERT.
- **Fallback:** If rate_limit node exists later, replace with node call.

### 4. Audit Scope Mandatory for DSAR
- **Example:** Operator (user_id=X, session_id=Y) triggers export of user_id=Z.
  ```json
  {
    "event_key": "iam.dsar.exported",
    "actor_user_id": "X",  // operator
    "session_id": "Y",
    "org_id": "...",
    "metadata": {
      "subject_user_id": "Z",
      "job_id": "...",
      "row_counts": {...}
    }
  }
  ```
- **Why:** Full audit trail of who accessed/deleted which user's data, when, from which session.

### 5. Delete Cascade Must Check deleted_at
- **Idempotency:** If user already soft-deleted (deleted_at IS NOT NULL), skip hard-delete.
- **Why:** Second request to delete same user should succeed silently, not error.
- **Pattern:**
  ```sql
  -- Soft-delete user (idempotent)
  UPDATE fct_users SET deleted_at = CURRENT_TIMESTAMP
  WHERE id = $1 AND deleted_at IS NULL;

  -- Hard-delete attrs (safe if already deleted)
  DELETE FROM dtl_attrs
  WHERE entity_id = $1 AND entity_type_id = 3;
  ```

---

## Testing Strategy (pytest)

### Test Fixtures Needed
```python
# conftest.py additions
@pytest.fixture
async def dsar_setup(pool):
    """Create test org, user, workspaces, audit events, etc."""
    org_id = uuid7()
    subject_user_id = uuid7()
    actor_user_id = uuid7()  # operator
    # ... seed tables
    yield {"org_id": org_id, "subject_user_id": subject_user_id, "actor_user_id": actor_user_id}
```

### Test Categories

1. **Export Request** (3 tests)
   - `test_export_request_creates_job` — check evt_dsar_jobs INSERT with status='requested'
   - `test_export_request_rate_limit` — 11th request returns 429
   - `test_export_nonexistent_user` — 404

2. **Delete Request** (3 tests)
   - `test_delete_request_cascades_all` — all dtl/lnk rows deleted
   - `test_delete_soft_deletes_user` — fct_users.deleted_at set
   - `test_delete_idempotent` — second delete succeeds

3. **Job Polling** (2 tests)
   - `test_poll_job_in_progress` — returns status + null result_location
   - `test_poll_job_completed` — returns status + result_location + download_url

4. **Export Data Shape** (2 tests)
   - `test_export_data_includes_all_tables` — JSON includes user, orgs, workspaces, sessions, audit_events
   - `test_export_data_valid_json` — parsed export is valid, not truncated

5. **Audit Emission** (2 tests)
   - `test_export_emits_audit` — evt_audit has `iam.dsar.exported` row
   - `test_delete_emits_audit` — evt_audit has `iam.dsar.deleted` row with counts

6. **Scope & Auth** (2 tests)
   - `test_export_cross_org_scope_denied` — 403 if actor not in org
   - `test_delete_cross_org_scope_denied` — 403 if actor not in org

**Total:** 14 tests, targeting 80%+ coverage.

---

## Files to Create/Modify

### New
- `03_docs/features/03_iam/05_sub_features/08_dsar/` (directory)
- `03_docs/features/03_iam/05_sub_features/08_dsar/09_sql_migrations/02_in_progress/20260421_071_dsar-jobs.sql`
- `backend/02_features/03_iam/sub_features/08_dsar/__init__.py`
- `backend/02_features/03_iam/sub_features/08_dsar/schemas.py`
- `backend/02_features/03_iam/sub_features/08_dsar/repository.py`
- `backend/02_features/03_iam/sub_features/08_dsar/service.py`
- `backend/02_features/03_iam/sub_features/08_dsar/routes.py`
- `tests/test_iam_dsar.py` (14+ tests)

### Modify
- `backend/02_features/03_iam/sub_features/19_gdpr/service.py` — add worker functions for DSAR
- `backend/02_features/03_iam/feature.manifest.yaml` — register sub_features/08_dsar
- `backend/main.py` — import DSAR router, register at `/v1/dsar`

### Documentation
- `03_docs/features/03_iam/05_sub_features/08_dsar/FEATURE.md` — brief overview

---

## Async/Await Patterns to Avoid Errors

### Pool Acquisition
```python
# ✓ Correct: acquire in route, pass conn to service
async with pool.acquire() as conn:
    result = await service.create_export_request(pool, conn, ctx, ...)
    
# ✗ Wrong: service acquires its own conn
async def create_export_request(pool, ...):
    async with pool.acquire() as conn:  # don't do this
        ...
```

### Audit Emission
```python
# ✓ Correct: use _catalog.run_node with proper context
await _catalog.run_node(
    pool, "audit.events.emit", ctx,
    {"event_key": "iam.dsar.exported", "outcome": "success", "metadata": {...}}
)

# ✗ Wrong: don't emit directly to DB without catalog
await conn.execute("INSERT INTO evt_audit ...")
```

### Vault Storage (for export)
```python
# Vault client should be available from request.app.state.vault
vault = request.app.state.vault
# Store: await vault.set_secret("iam.dsar.export.{job_id}", data, ttl_seconds=7776000)
# Retrieve + sign: await vault.get_signed_url("iam.dsar.export.{job_id}")
```

---

## Validation Before Code Generation

**Checklist before implementing:**
- [ ] Migration 071 SQL is correct (indexes, constraints, COMMENT ON every column)
- [ ] schemas.py models match PLAN exactly (no extra fields)
- [ ] repository.py functions use correct SQL patterns (conn not pool, raw SQL)
- [ ] service.py async functions properly use pool/conn lifecycle
- [ ] routes.py context building includes audit_category and workspace_id
- [ ] Rate limit logic is clear and testable
- [ ] Delete cascade is idempotent (checked deleted_at before UPDATE)
- [ ] Audit scope includes user_id + session_id + org_id + workspace_id
- [ ] Worker loop integration doesn't break existing GDPR jobs

---

## Success Criteria (from PLAN.md)

- [ ] `POST /v1/dsar/export-request` creates async job, returns job_id
- [ ] `GET /v1/dsar/jobs/{id}` polls status + download URL when complete
- [ ] Export includes: user + orgs + workspaces + sessions + audit events + notification subscriptions
- [ ] Export format: JSON (one object, not lines)
- [ ] `POST /v1/dsar/delete-request` hard-deletes all user data atomically; soft-deletes user
- [ ] Delete is idempotent (re-running does nothing)
- [ ] Both ops write audit events: `iam.dsar.exported` / `iam.dsar.deleted`
- [ ] Rate limit: 10 DSAR ops per org per hour
- [ ] All data removed from Postgres
- [ ] pytest green (80%+ coverage)
- [ ] pyright exit 0
