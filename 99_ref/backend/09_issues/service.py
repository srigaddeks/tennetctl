"""Issue service — auto-creates issues from failed control tests, manages lifecycle."""
from __future__ import annotations

import json
import uuid
from importlib import import_module

from .schemas import IssueListResponse, IssueResponse, IssueStatsResponse, UpdateIssueRequest

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError

SCHEMA = '"09_issues"'
logger = get_logger(__name__)


def _row_to_response(r) -> IssueResponse:
    details = r.get("result_details")
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except (json.JSONDecodeError, TypeError):
            details = None
    return IssueResponse(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        org_id=str(r["org_id"]),
        workspace_id=str(r["workspace_id"]) if r.get("workspace_id") else None,
        promoted_test_id=str(r["promoted_test_id"]) if r.get("promoted_test_id") else None,
        control_test_id=str(r["control_test_id"]) if r.get("control_test_id") else None,
        execution_id=str(r["execution_id"]) if r.get("execution_id") else None,
        connector_id=str(r["connector_id"]) if r.get("connector_id") else None,
        status_code=r["status_code"],
        severity_code=r["severity_code"],
        issue_code=r["issue_code"],
        test_code=r.get("test_code"),
        test_name=r.get("test_name"),
        result_summary=r.get("result_summary"),
        result_details=details if isinstance(details, list) else None,
        connector_type_code=r.get("connector_type_code"),
        assigned_to=str(r["assigned_to"]) if r.get("assigned_to") else None,
        remediated_at=str(r["remediated_at"]) if r.get("remediated_at") else None,
        remediation_notes=r.get("remediation_notes"),
        verified_at=str(r["verified_at"]) if r.get("verified_at") else None,
        is_active=r["is_active"],
        created_at=str(r["created_at"]),
        updated_at=str(r["updated_at"]),
        closed_at=str(r["closed_at"]) if r.get("closed_at") else None,
    )


@instrument_class_methods(namespace="issues.service", logger_name="backend.issues.service.instrumentation")
class IssueService:
    def __init__(self, *, database_pool: DatabasePool):
        self._pool = database_pool

    # ── auto-create from test failure ─────────────────────────────

    async def create_from_test_failure(
        self,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        promoted_test_id: str,
        control_test_id: str | None,
        execution_id: str | None,
        connector_id: str | None,
        test_code: str,
        test_name: str | None,
        result_summary: str,
        result_details: list | None,
        connector_type_code: str | None,
        severity_code: str = "high",
        created_by: str | None = None,
    ) -> str:
        """Create an issue from a failed control test execution. Returns issue_id or existing issue_id if duplicate."""
        async with self._pool.transaction() as conn:
            # Check for existing non-closed issue for this same test_code — prevent duplicates
            existing = await conn.fetchrow(f"""
                SELECT id, status_code FROM {SCHEMA}."10_fct_issues"
                WHERE test_code = $1 AND org_id = $2
                  AND status_code NOT IN ('closed', 'accepted')
                  AND is_active = TRUE AND is_deleted = FALSE
                ORDER BY created_at DESC LIMIT 1
            """, test_code, org_id)
            if existing:
                # Update the existing issue with latest execution details — don't create duplicate
                await conn.execute(f"""
                    UPDATE {SCHEMA}."10_fct_issues"
                    SET execution_id = $1, result_summary = $2, result_details = $3::jsonb,
                        updated_at = NOW(), severity_code = $4
                    WHERE id = $5
                """, execution_id, result_summary,
                    json.dumps(result_details) if result_details else None,
                    severity_code, str(existing["id"]))
                logger.info(f"issue_updated_existing: {existing['id']} for test {test_code} (status: {existing['status_code']})")
                return str(existing["id"])

            # Generate issue code: ISS-YYYY-NNN
            from datetime import datetime, timezone
            year = datetime.now(timezone.utc).year
            seq_row = await conn.fetchrow(f"SELECT nextval('{SCHEMA}.\"issue_code_seq\"')::int AS seq")
            seq = seq_row["seq"] if seq_row else 1
            issue_code = f"ISS-{year}-{seq:04d}"

            issue_id = str(uuid.uuid4())
            await conn.execute(f"""
                INSERT INTO {SCHEMA}."10_fct_issues"
                    (id, tenant_key, org_id, workspace_id,
                     promoted_test_id, control_test_id, execution_id, connector_id,
                     status_code, severity_code, issue_code,
                     test_code, test_name, result_summary, result_details,
                     connector_type_code, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'open', $9, $10, $11, $12, $13, $14::jsonb, $15, $16)
            """,
                issue_id, tenant_key, org_id, workspace_id,
                promoted_test_id, control_test_id, execution_id, connector_id,
                severity_code, issue_code,
                test_code, test_name, result_summary,
                json.dumps(result_details) if result_details else None,
                connector_type_code, created_by,
            )
            logger.info(f"issue_created: {issue_code} for test {test_code}", extra={"action": "issue.create", "issue_code": issue_code})
            return issue_id

    # ── list ──────────────────────────────────────────────────────

    async def list_issues(
        self, *, org_id: str,
        status_code: str | None = None,
        severity_code: str | None = None,
        connector_id: str | None = None,
        search: str | None = None,
        limit: int = 100, offset: int = 0,
    ) -> IssueListResponse:
        async with self._pool.acquire() as conn:
            filters = ["org_id = $1", "is_active = TRUE", "is_deleted = FALSE"]
            values: list[object] = [org_id]
            idx = 2
            if status_code:
                filters.append(f"status_code = ${idx}")
                values.append(status_code)
                idx += 1
            if severity_code:
                filters.append(f"severity_code = ${idx}")
                values.append(severity_code)
                idx += 1
            if connector_id:
                filters.append(f"connector_id = ${idx}")
                values.append(connector_id)
                idx += 1
            if search:
                filters.append(f"(test_name ILIKE ${idx} OR test_code ILIKE ${idx} OR issue_code ILIKE ${idx} OR result_summary ILIKE ${idx})")
                values.append(f"%{search}%")
                idx += 1

            where = " AND ".join(filters)
            count_row = await conn.fetchrow(f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."10_fct_issues" WHERE {where}', *values)
            total = count_row["total"] if count_row else 0

            rows = await conn.fetch(
                f'SELECT * FROM {SCHEMA}."10_fct_issues" WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx+1}',
                *values, limit, offset,
            )
            return IssueListResponse(items=[_row_to_response(r) for r in rows], total=total)

    # ── get ───────────────────────────────────────────────────────

    async def get_issue(self, issue_id: str) -> IssueResponse:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f'SELECT * FROM {SCHEMA}."10_fct_issues" WHERE id = $1 AND is_active AND NOT is_deleted', issue_id)
            if not row:
                raise NotFoundError("Issue not found")
            return _row_to_response(row)

    # ── update status ────────────────────────────────────────────

    async def update_issue(self, issue_id: str, request: UpdateIssueRequest, user_id: str) -> IssueResponse:
        async with self._pool.transaction() as conn:
            row = await conn.fetchrow(f'SELECT * FROM {SCHEMA}."10_fct_issues" WHERE id = $1 AND is_active AND NOT is_deleted', issue_id)
            if not row:
                raise NotFoundError("Issue not found")

            sets = ["updated_at = NOW()"]
            values: list[object] = []
            idx = 1
            if request.status_code:
                sets.append(f"status_code = ${idx}")
                values.append(request.status_code)
                idx += 1
                if request.status_code == "remediated":
                    sets.append(f"remediated_at = NOW()")
                    sets.append(f"remediated_by = ${idx}")
                    values.append(user_id)
                    idx += 1
                elif request.status_code == "verified":
                    sets.append(f"verified_at = NOW()")
                    sets.append(f"verified_by = ${idx}")
                    values.append(user_id)
                    idx += 1
                elif request.status_code in ("closed", "accepted"):
                    sets.append(f"closed_at = NOW()")
            if request.severity_code:
                sets.append(f"severity_code = ${idx}")
                values.append(request.severity_code)
                idx += 1
            if request.assigned_to:
                sets.append(f"assigned_to = ${idx}")
                values.append(request.assigned_to)
                idx += 1
            if request.remediation_notes:
                sets.append(f"remediation_notes = ${idx}")
                values.append(request.remediation_notes)
                idx += 1

            values.append(issue_id)
            await conn.execute(f'UPDATE {SCHEMA}."10_fct_issues" SET {", ".join(sets)} WHERE id = ${idx}', *values)

            updated = await conn.fetchrow(f'SELECT * FROM {SCHEMA}."10_fct_issues" WHERE id = $1', issue_id)
            return _row_to_response(updated)

    # ── stats ────────────────────────────────────────────────────

    async def get_stats(self, org_id: str) -> IssueStatsResponse:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"""
                SELECT
                    COUNT(*)::int AS total,
                    COUNT(*) FILTER (WHERE status_code = 'open')::int AS open,
                    COUNT(*) FILTER (WHERE status_code = 'investigating')::int AS investigating,
                    COUNT(*) FILTER (WHERE status_code = 'remediated')::int AS remediated,
                    COUNT(*) FILTER (WHERE status_code IN ('closed', 'accepted', 'verified'))::int AS closed
                FROM {SCHEMA}."10_fct_issues"
                WHERE org_id = $1 AND is_active AND NOT is_deleted
            """, org_id)

            sev_rows = await conn.fetch(f"""
                SELECT severity_code, COUNT(*)::int AS cnt
                FROM {SCHEMA}."10_fct_issues"
                WHERE org_id = $1 AND is_active AND NOT is_deleted AND status_code NOT IN ('closed', 'accepted')
                GROUP BY severity_code
            """, org_id)

            ct_rows = await conn.fetch(f"""
                SELECT connector_type_code, COUNT(*)::int AS cnt
                FROM {SCHEMA}."10_fct_issues"
                WHERE org_id = $1 AND is_active AND NOT is_deleted AND connector_type_code IS NOT NULL
                GROUP BY connector_type_code
            """, org_id)

            return IssueStatsResponse(
                total=row["total"] if row else 0,
                open=row["open"] if row else 0,
                investigating=row["investigating"] if row else 0,
                remediated=row["remediated"] if row else 0,
                closed=row["closed"] if row else 0,
                by_severity={r["severity_code"]: r["cnt"] for r in sev_rows},
                by_connector_type={r["connector_type_code"]: r["cnt"] for r in ct_rows},
            )
