# Phase 45 — GDPR DSAR

**Milestone:** v0.8.0 OSS Compliance  
**Status:** PLANNING COMPLETE (ready for 45-01-APPLY)  
**Created:** 2026-04-21  

---

## Quick Start

**Planning complete.** Two comprehensive plans drafted:

- **45-01-PLAN.md** — Backend operator API (export + delete, v0.8.0 gate)
- **45-02-PLAN.md** — Self-service portal (deferred to v1.0)

**Ready to implement:** Run `paul:apply 45-01-PLAN.md` to begin 45-01 implementation (~90 min).

---

## Files in This Phase

| File | Purpose | Status |
|------|---------|--------|
| `45-01-PLAN.md` | Operator-triggered DSAR backend (export/delete/audit/rate limit) | ✅ Ready for apply |
| `45-02-PLAN.md` | Self-service portal + 30-day recovery (deferred v1.0) | ✅ Reference only |
| `PLANNING-SUMMARY.md` | Decision rationale, data structures, testing strategy | ✅ Reference |
| `CONTEXT.md` | Original context (v0.5.0 product_ops era, now superseded) | ⚠️ Legacy |

---

## What This Phase Does

Implements GDPR Article 12 compliance (Data Subject Access Request) for the TennetCTL platform. Users must be able to:

1. **Export their data** in machine-readable format within 30 days
2. **Delete their data** (hard-erase) upon request

**Scope (v0.8.0):** Operator-triggered API only. Operators can request exports/deletes on behalf of users.  
**Deferred (v1.0):** Self-service portal where users can request their own exports/deletes with 2FA + 30-day recovery window.

---

## 45-01: Backend Operator API

### What Ships

- **Schema:** `evt_dsar_jobs` table (immutable event log of all DSAR requests)
- **Sub-feature:** `iam.dsar` (5 files: schemas, repo, service, routes, __init__)
- **Export endpoint:** `POST /v1/dsar/export-request` → async job → JSON in vault
- **Delete endpoint:** `POST /v1/dsar/delete-request` → hard-delete cascade (idempotent)
- **Poll endpoint:** `GET /v1/dsar/jobs/{id}` → check status + download URL
- **List endpoint:** `GET /v1/dsar/jobs` → filtered by org + workspace scope
- **Audit nodes:** `iam.dsar.exported` + `iam.dsar.deleted` (effect nodes, emits_audit=true)
- **Rate limit:** 10 DSAR ops per workspace per hour (reuses core.rate_limit.check)
- **Tests:** 15+ unit tests covering all flows

### Export Flow

1. Operator calls `POST /v1/dsar/export-request`
2. Backend creates `evt_dsar_jobs` record with status=requested
3. Async job dispatcher starts background task
4. Export aggregates: user + orgs + workspaces + sessions + audit events + subscriptions
5. JSON written to vault at `iam.dsar.{job_id}` (90-day TTL)
6. Job status → completed
7. Operator polls `GET /v1/dsar/jobs/{id}` → gets signed download URL
8. Audit event emitted: `iam.dsar.exported` with row counts

### Delete Flow

1. Operator calls `POST /v1/dsar/delete-request`
2. Backend creates `evt_dsar_jobs` record with status=requested
3. Delete service runs in single transaction:
   - Hard-delete from dtl_*, lnk_*, evt_audit rows
   - Soft-delete user (set deleted_at)
4. Row counts captured and stored in evt_dsar_jobs
5. Job status → completed
6. Audit event emitted: `iam.dsar.deleted` with counts
7. Idempotent: re-running returns 200, no error

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Export as JSON (not CSV/ZIP) | Simpler format, easier to parse; JSON Lines is streaming-safe |
| Store export in vault | Secure storage with signed download URLs; 90-day TTL prevents stale data |
| Hard-delete satellite data | GDPR requires actual erasure, not just deactivation |
| Soft-delete user | Preserves audit trail (FK refs in evt_audit.created_by); user invisible in app |
| Single transaction for delete | Atomic delete (no partial failures); tight, fast, testable |
| Idempotent delete | Safe to re-run (no 409 Conflict); matches REST best practices |
| Reuse rate_limit.check | Proven node from Phase 38; prevents DoS of export service |
| Two audit nodes | Captures complete audit trail of who accessed/deleted whose data |

### Acceptance Criteria

- [ ] Migration 071 applied (`evt_dsar_jobs` table exists)
- [ ] Export request creates job with status=requested
- [ ] Export async job completes, result_location populated
- [ ] Export JSON valid and complete (all tables included)
- [ ] Delete request cascades hard-delete across all tables
- [ ] Delete soft-deletes user record (deleted_at set)
- [ ] Re-running delete is idempotent
- [ ] Rate limit enforced (10/hr per org)
- [ ] Both ops emit audit events
- [ ] pytest tests green (15+ tests, 80%+ coverage)
- [ ] pyright exit 0

---

## 45-02: Self-Service Portal (Deferred to v1.0)

### Why Deferred

45-01 alone satisfies GDPR Article 12 compliance. Self-hosted TennetCTL deployments (primary users) have direct operator access — they can request exports/deletes directly. Self-service portal is a UX feature needed only for:

- Public SaaS wrapping of TennetCTL (v1.0 scope)
- Enterprise deployments with user self-service access

Deferring keeps v0.8.0 scope tight and enables faster shipping to open-source readiness.

### What 45-02 Adds (v1.0)

1. **Self-service endpoints:**  
   - `POST /v1/account/data-export` — current user requests their own export
   - `POST /v1/account/delete-me` — current user requests account deletion
   - `POST /v1/account/cancel-deletion` — cancel deletion within 30-day window

2. **Recovery window:**  
   - User deletion: soft-delete user immediately, hard-erase after 30 days
   - User can cancel within window (set deleted_at = NULL)
   - Operator deletion: hard-erase immediately (no recovery)

3. **2FA verification:**  
   - Export requires session + 2FA check (if enabled)
   - Delete requires password re-entry + 2FA challenge

4. **Email notifications:**  
   - Export ready (with download link)
   - Deletion initiated (with recovery window countdown)
   - Deletion final notice (day 29, last chance to cancel)
   - Deletion completed (after 30 days)

5. **User-facing UI:**  
   - `/account/data` — export status + delete request form
   - `/iam/dsar` — operator dashboard (job history, new requests)

6. **Background scheduler:**  
   - 30-day purge job (auto-delete after recovery window)
   - Runs daily, hard-erases expired deletions

### 45-02 Files

- Routes: `routes_self_service.py` + `routes_operator.py` (extending 45-01)
- Background: `background_jobs.py` (30-day purge scheduler)
- Frontend: Account settings page + operator dashboard
- Hooks: TanStack Query hooks for job polling + creation
- Components: Export/delete dialogs + job tables
- Tests: 25+ unit tests + 8 Playwright E2E scenarios
- Effort: ~120 min, ~1100 lines code

---

## Test Coverage

### 45-01 Unit Tests (15+)

```
test_export_request_creates_job
test_export_request_rate_limit
test_export_request_not_found
test_delete_request_cascades_all_rows
test_delete_request_soft_deletes_user
test_delete_request_idempotent
test_poll_job_in_progress
test_poll_job_completed
test_export_includes_all_tables
test_export_json_valid
test_export_emits_audit
test_delete_emits_audit
test_export_nonexistent_user
test_delete_nonexistent_user
test_export_cross_org_scope_denied
test_delete_cross_org_scope_denied
```

**No Playwright E2E:** 45-01 is backend-only (operator API). E2E testing deferred to 45-02 (frontend/portal).

### 45-02 Unit Tests (25+) + E2E (8 scenarios)

Unit tests cover:
- User self-service export
- User self-service delete + 2FA
- Deletion cancellation within window
- Background purge job
- Operator override (immediate delete, no recovery)
- Email notifications
- Rate limiting
- Vault signed URLs

E2E scenarios cover:
- Operator export flow (request → polling → download)
- User delete flow (request → 2FA → recovery window)
- User cancel deletion within window
- Operator delete (immediate)
- 30-day background purge
- Rate limit enforcement
- Email notifications

---

## Implementation Roadmap

### Phase 45-01 (This Session, ~90 min)

```
START
  ├─ Create migration 071 (evt_dsar_jobs)
  ├─ Implement schemas.py (Pydantic models)
  ├─ Implement repository.py (SQL queries)
  ├─ Implement service.py (business logic + async dispatch)
  ├─ Implement routes.py (FastAPI handlers)
  ├─ Update feature.manifest.yaml (register sub-feature + 2 nodes)
  ├─ Write unit tests (test_iam_dsar.py)
  ├─ Run pytest + pyright (verify green)
  └─ DONE: 45-01-SUMMARY.md written
```

### Phase 45-02 (v1.0 roadmap, deferred)

- Add self-service routes
- Add background job scheduler
- Build frontend UI
- Write E2E tests
- Integrate email notifications

---

## Quick Reference

### Export Data Model

```json
{
  "user": {id, email, display_name, created_at, deleted_at},
  "organizations": [{id, name, role, created_at}],
  "workspaces": [{id, org_id, name, role, created_at}],
  "workspace_members": [{workspace_id, role, created_at}],
  "sessions": [{id, created_at, expires_at, last_activity_at, ip_address, user_agent}],
  "audit_events": [{event_key, outcome, category, attributes, created_at}],
  "notification_subscriptions": [{id, channel, created_at}]
}
```

### Delete Cascade (Single Transaction)

```
Hard-delete from:
  ├─ dtl_user_attrs (EAV)
  ├─ lnk_workspace_members (ACL)
  ├─ lnk_org_members (ACL)
  ├─ evt_audit rows (where actor_id = user)
  ├─ fct_sessions (soft-delete: set logged_out_at)
  └─ dtl_notification_subscriptions

Soft-delete:
  └─ fct_users (set deleted_at)
```

### Rate Limit

```
Key: dsar.{org_id}
Limit: 10 per hour per workspace
Exceeds: 429 Conflict
Reuses: core.rate_limit.check (Phase 38)
```

---

## Related Documents

- **45-01-PLAN.md** — Full technical specification of backend implementation
- **45-02-PLAN.md** — Full specification of self-service portal (v1.0)
- **PLANNING-SUMMARY.md** — Design decisions, data structures, testing strategy
- **.paul/ROADMAP.md** — v0.8.0 milestone overview
- **.paul/STATE.md** — Current project status

---

## Status

✅ **Planning complete** (2026-04-21)

Next action: `paul:apply 45-01-PLAN.md`
