# Phase 45 Planning Summary — GDPR DSAR

**Created:** 2026-04-21  
**Status:** PLANNING COMPLETE (PENDING-APPLY)  
**Milestone:** v0.8.0 OSS Compliance  

---

## Overview

Phase 45 breaks down GDPR Data Subject Access Request (DSAR) compliance into two focused plans:

- **45-01 (Backend)** — operator-triggered export + delete + audit + rate limiting (v0.8.0 gate)  
- **45-02 (Frontend + Self-Service)** — user-facing portal with 30-day recovery window (deferred to v1.0)

---

## Decision Summary

### What's In (45-01, v0.8.0)

✅ **Export Flow**  
- Async job-based architecture (background task)  
- JSON Lines format (streaming-safe)  
- Includes: user + orgs + workspaces + sessions + audit events + subscriptions  
- Stored in vault with 90-day TTL  

✅ **Delete Flow**  
- Single-transaction hard-delete cascade  
- Soft-deletes user record (deleted_at), hard-deletes all satellite data  
- Idempotent (safe to re-run)  

✅ **Audit Emission**  
- New node kinds: `iam.dsar.exported` / `iam.dsar.deleted`  
- Captures row counts + actor/subject + org scope  

✅ **Rate Limiting**  
- Reuses PG-native rate_limit from Phase 38  
- 10 DSAR ops per workspace per hour  

✅ **Routes**  
- `POST /v1/dsar/export-request` (operator-triggered)  
- `POST /v1/dsar/delete-request` (operator-triggered)  
- `GET /v1/dsar/jobs/{id}` (poll status + download)  
- `GET /v1/dsar/jobs` (list with org scope)

### What's Deferred (45-02, v1.0)

❌ Self-service endpoints (`/v1/account/data-export`, `/v1/account/delete-me`)  
❌ 2FA verification on sensitive ops  
❌ 30-day recovery window before hard-erase  
❌ Email notifications (export ready, deletion initiated, final notice)  
❌ User-facing UI (`/account/data`, `/iam/dsar` operator dashboard)  
❌ Admin page for DSAR history  

**Rationale:** v0.8.0 is the "OSS readiness gate" — only needs operator-facing APIs to satisfy GDPR/CCPA requirements. Self-service portal is a UX feature deferred to v1.0 once core compliance is proven.

---

## Schema Design

### New Table: `evt_dsar_jobs`

Immutable append-only event table:

```sql
evt_dsar_jobs (
  job_id UUID v7 PRIMARY KEY,
  job_type TEXT (export|delete),
  actor_user_id UUID v7,           -- who triggered
  subject_user_id UUID v7,         -- whose data
  org_id UUID v7,
  status TEXT (requested|in_progress|completed|failed),
  row_counts JSONB,                -- {org: 1, workspace: 3, audit_events: 127}
  error_message TEXT,              -- null unless failed
  result_location TEXT,            -- vault key like iam.dsar.export.{job_id}
  created_at, completed_at TIMESTAMP,
  created_by UUID v7,              -- for audit scope
  is_test BOOLEAN
)
```

**Why evt_ prefix?** DSAR jobs are system events (audit trail). Immutable records of every data access request, compliant with GDPR Article 12 (right to know who accessed your data).

---

## Export Data Model

Single JSON object per user:

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

**Format:** JSON Lines (one record per line), not a single array. Safer for large datasets (streaming-friendly, bounded memory).

---

## Delete Cascade

Hard-delete from:
- `dtl_user_attrs` (EAV attributes)  
- `lnk_workspace_members` (workspace acl)  
- `lnk_org_members` (org acl, if exists)  
- `evt_audit` rows where actor_id = user (audit-of-user's-actions)  
- `fct_sessions` (soft-delete: set logged_out_at)  
- `dtl_notification_subscriptions` (notification prefs)  

Soft-delete:
- `fct_users` (set deleted_at, preserve identity for audit trail)

**Why soft-delete user?** Audit trail must reference the user who acted. Hard-deleting fct_users would break FK refs in evt_audit.created_by. Solution: soft-delete user (invisible in app), keep FK refs valid.

---

## Rate Limiting

Reuses Phase 38's `core.rate_limit.check` node:

```python
rl = await run_node(pool, "core.rate_limit.check", ctx, {
    "key": f"dsar.{org_id}",
    "action": "export|delete",
    "limit": 10,
    "window_seconds": 3600
})
```

Returns `allowed: bool`. If false, HTTP 429 Conflict.

**Scope:** Per workspace/org, not global. Allows large orgs to request more in parallel.

---

## Audit Emission

Two new node kinds registered in manifest:

| Node | Kind | Input | Output | Purpose |
|------|------|-------|--------|---------|
| `iam.dsar.exported` | effect | {job_id, counts} | — | Emit audit event after export completes |
| `iam.dsar.deleted` | effect | {job_id, counts} | — | Emit audit event after delete completes |

Both `emits_audit=true` (mandatory for effects). Called by service after job completes:

```python
await run_node(pool, "iam.dsar.exported", ctx, {
    "job_id": job_id,
    "row_counts": {"audit_events": 127, "sessions": 5, ...}
})
```

---

## Testing Strategy

### 45-01 Tests (15+ unit tests)

1. **Export Request**  
   - Creates job with status=requested  
   - Rate limit enforced (11th request → 429)  
   - User not found → 404

2. **Delete Request**  
   - Cascades hard-delete across all tables  
   - Soft-deletes user record  
   - Idempotent (re-run succeeds)  

3. **Job Polling**  
   - In-progress job returns status + null result_location  
   - Completed job returns status + result_location + download URL  

4. **Export Data Shape**  
   - Seeded user has rows in all tables  
   - Export JSON includes all tables  
   - JSON is valid and not truncated  

5. **Audit**  
   - Export emits `iam.dsar.exported` audit row  
   - Delete emits `iam.dsar.deleted` audit row with counts  

6. **Edge Cases**  
   - Cross-org scope denied (403)  
   - Nonexistent user (404)  
   - Rate limit boundary (10th request succeeds, 11th fails)

### No Playwright E2E for 45-01

Operator-triggered flows don't have a natural user journey to walk through in the browser. E2E testing is deferred to 45-02 (frontend/portal).

---

## Implementation Sequence (45-01)

1. **Migration 071** — Create evt_dsar_jobs table  
2. **Schemas** — Pydantic models for request/response  
3. **Repository** — SQL queries (insert job, update status, export/delete cascades)  
4. **Service** — Business logic (rate limit check, async dispatch, job completion)  
5. **Routes** — FastAPI handlers (POST/GET endpoints)  
6. **Manifest** — Register 2 nodes + sub-feature  
7. **Tests** — Unit tests for all flows  
8. **Integration** — Wire routes into main.py, background task scheduler  

Estimated: **60–90 min** for full 45-01 (schema + code + tests).

---

## Why v0.8.0 (Not v1.0)

GDPR Article 12 requires "a copy of the personal data undergoing processing in an intelligible form" within 30 days of request. TennetCTL must provide this, or fail EU legal compliance. Making it operator-triggered (vs self-service) is acceptable for v0.8.0 because:

1. Self-hosted deployments (primary TennetCTL customers) have direct admin access  
2. Adding 2FA verification + 30-day recovery is UI complexity, not compliance requirement  
3. Self-service portal becomes table-stakes in v1.0 (public SaaS wrapping)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Export too large (OOM) | Chunked reads by created_at partition; async job with disk storage |
| Delete foreign key violations | Single transaction; test cascade on populated DB |
| Rate limit bypass | Reuse battle-tested core.rate_limit.check node |
| Audit trail lost | Soft-delete user (not hard-delete) + FK refs preserved |
| User data leaked (insecure download) | Vault storage + signed URLs + 90-day expiration |
| Recovery window confusion (v1.0) | Document clearly: operator delete = immediate, user delete = 30-day window |

---

## Known Unknowns (Deferred to 45-02 or v1.0)

1. **Email template design** — Exact wording for "30 days to cancel" email (legal review needed)  
2. **CCPA opt-out semantics** — Delete vs anonymize (tracked in memory)  
3. **Cross-feature DSAR** — Should deleting a user also delete their feature flag edits? (v2.0 scope)  
4. **Retention SLA** — Keep audit trail forever, or 7-year legal minimum?  

---

## Files Summary

### 45-01 (Backend) — 6 files

| File | Lines | Purpose |
|------|-------|---------|
| `09_sql_migrations/20260421_071_dsar.sql` | 30 | evt_dsar_jobs table + view |
| `sub_features/08_dsar/__init__.py` | 5 | — |
| `sub_features/08_dsar/schemas.py` | 40 | Pydantic models |
| `sub_features/08_dsar/repository.py` | 150 | SQL queries |
| `sub_features/08_dsar/service.py` | 200 | Business logic + async dispatch |
| `sub_features/08_dsar/routes.py` | 80 | FastAPI handlers |

**Total new code:** ~500 lines  
**Test code:** ~400 lines  

### 45-02 (Frontend + Portal) — 12 files (deferred)

| File | Lines | Purpose |
|------|-------|---------|
| `routes_self_service.py` | 120 | /v1/account/* endpoints |
| `routes_operator.py` | 100 | /v1/iam/dsar/* endpoints |
| `background_jobs.py` | 80 | 30-day purge scheduler |
| `{account,iam}/page.tsx` | 300 | UI pages |
| `hooks/use-dsar-*.ts` | 150 | TanStack Query hooks |
| `components/Dsar*.tsx` | 200 | Form + table components |
| `tests/e2e/dsar.robot` | 150 | Playwright E2E |

**Total new code:** ~1100 lines  
**Test code:** ~150 lines  

---

## Approval Gate

Phase 45 planning is complete. Ready to `paul:apply 45-01-PLAN.md` whenever the user confirms:

- [ ] Scope of 45-01 (backend operator API) vs 45-02 (deferred portal) is acceptable  
- [ ] Export as JSON Lines format matches requirements  
- [ ] 30-day recovery window should be deferred to v1.0  
- [ ] Rate limit of 10 per hour per org is reasonable  

If approved, implementation can begin immediately.
