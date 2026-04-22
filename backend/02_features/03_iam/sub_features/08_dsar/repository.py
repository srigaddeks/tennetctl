"""
iam.dsar — asyncpg repository.

Reads + writes "03_iam"."65_evt_dsar_jobs" (append-only events).
All ID columns are VARCHAR(36) for consistency with IAM schema.
"""

from __future__ import annotations

from typing import Any


_JOBS_TABLE = '"03_iam"."65_evt_dsar_jobs"'
_TYPES_DIM = '"03_iam"."08_dim_dsar_types"'
_STATUSES_DIM = '"03_iam"."07_dim_dsar_statuses"'
_PAYLOADS_TABLE = '"03_iam"."20_dtl_dsar_payloads"'


async def _type_id(conn: Any, code: str) -> int:
    """Look up dim_dsar_types by code."""
    row = await conn.fetchrow(f"SELECT id FROM {_TYPES_DIM} WHERE code = $1", code)
    if row is None:
        raise RuntimeError(f"dsar type not found: {code}")
    return int(row["id"])


async def _status_id(conn: Any, code: str) -> int:
    """Look up dim_dsar_statuses by code."""
    row = await conn.fetchrow(f"SELECT id FROM {_STATUSES_DIM} WHERE code = $1", code)
    if row is None:
        raise RuntimeError(f"dsar status not found: {code}")
    return int(row["id"])


async def create_dsar_job(
    conn: Any,
    *,
    job_id: str,
    org_id: str,
    subject_user_id: str,
    actor_user_id: str,
    job_type: str,
    actor_session_id: str | None = None,
) -> None:
    """Create a new DSAR job (INSERT to evt_dsar_jobs)."""
    type_id = await _type_id(conn, job_type)
    status_id = await _status_id(conn, "requested")
    await conn.execute(
        f"INSERT INTO {_JOBS_TABLE} "
        "(id, org_id, subject_user_id, actor_user_id, actor_session_id, job_type_id, status_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7)",
        job_id, org_id, subject_user_id, actor_user_id, actor_session_id, type_id, status_id,
    )


async def get_dsar_job(conn: Any, job_id: str) -> dict | None:
    """Fetch a single DSAR job by ID (read view with dim lookups)."""
    row = await conn.fetchrow(
        f"SELECT j.id, j.org_id, j.subject_user_id, j.actor_user_id, j.actor_session_id, "
        "       t.code AS job_type, s.code AS status, "
        "       j.row_counts, j.result_location, j.error_detail, j.completed_at, j.created_at "
        f"FROM {_JOBS_TABLE} j "
        f"JOIN {_TYPES_DIM} t ON t.id = j.job_type_id "
        f"JOIN {_STATUSES_DIM} s ON s.id = j.status_id "
        "WHERE j.id = $1",
        job_id,
    )
    return dict(row) if row else None


async def list_dsar_jobs(
    conn: Any,
    org_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List DSAR jobs for an org with pagination."""
    # Get total count
    count_row = await conn.fetchval(
        f"SELECT COUNT(*) FROM {_JOBS_TABLE} WHERE org_id = $1",
        org_id,
    )
    total = int(count_row) if count_row else 0

    # Fetch paginated results
    rows = await conn.fetch(
        f"SELECT j.id, j.org_id, j.subject_user_id, j.actor_user_id, j.actor_session_id, "
        "       t.code AS job_type, s.code AS status, "
        "       j.row_counts, j.result_location, j.error_detail, j.completed_at, j.created_at "
        f"FROM {_JOBS_TABLE} j "
        f"JOIN {_TYPES_DIM} t ON t.id = j.job_type_id "
        f"JOIN {_STATUSES_DIM} s ON s.id = j.status_id "
        "WHERE j.org_id = $1 "
        "ORDER BY j.created_at DESC LIMIT $2 OFFSET $3",
        org_id, limit, offset,
    )
    return [dict(r) for r in rows], total


async def update_dsar_job_status(
    conn: Any,
    *,
    job_id: str,
    status: str,
    row_counts: dict | None = None,
    result_location: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Update DSAR job status (idempotent: only transitions to new status)."""
    status_id = await _status_id(conn, status)
    await conn.execute(
        f"UPDATE {_JOBS_TABLE} "
        "SET status_id = $1::smallint, "
        "    row_counts = COALESCE($2::JSONB, row_counts), "
        "    result_location = COALESCE($3, result_location), "
        "    error_detail = COALESCE($4, error_detail), "
        "    completed_at = CASE WHEN $1::smallint IN (3, 4) AND completed_at IS NULL "
        "                       THEN CURRENT_TIMESTAMP ELSE completed_at END "
        "WHERE id = $5",
        status_id, row_counts, result_location, error_detail, job_id,
    )


async def list_pending_exports(conn: Any, limit: int = 10) -> list[dict]:
    """Find export jobs in 'requested' status."""
    rows = await conn.fetch(
        f"SELECT j.id, j.org_id, j.subject_user_id, j.actor_user_id "
        f"FROM {_JOBS_TABLE} j "
        f"JOIN {_TYPES_DIM} t ON t.id = j.job_type_id "
        f"JOIN {_STATUSES_DIM} s ON s.id = j.status_id "
        "WHERE t.code = 'export' AND s.code = 'requested' "
        "ORDER BY j.created_at ASC LIMIT $1",
        limit,
    )
    return [dict(r) for r in rows]


async def list_pending_deletes(conn: Any, limit: int = 10) -> list[dict]:
    """Find delete jobs in 'requested' status."""
    rows = await conn.fetch(
        f"SELECT j.id, j.org_id, j.subject_user_id, j.actor_user_id "
        f"FROM {_JOBS_TABLE} j "
        f"JOIN {_TYPES_DIM} t ON t.id = j.job_type_id "
        f"JOIN {_STATUSES_DIM} s ON s.id = j.status_id "
        "WHERE t.code = 'delete' AND s.code = 'requested' "
        "ORDER BY j.created_at ASC LIMIT $1",
        limit,
    )
    return [dict(r) for r in rows]


async def user_belongs_to_org(conn: Any, user_id: str, org_id: str) -> bool:
    """Check if a user has any membership in the org."""
    row = await conn.fetchval(
        'SELECT 1 FROM "03_iam"."40_lnk_org_members" '
        "WHERE org_id = $1 AND user_id = $2 LIMIT 1",
        org_id, user_id,
    )
    return row is not None


async def check_rate_limit(conn: Any, org_id: str) -> bool:
    """
    Check if org has reached rate limit (10 DSAR requests per hour).
    Returns True if under limit, False if at/over limit.
    """
    count = await conn.fetchval(
        f"SELECT COUNT(*) FROM {_JOBS_TABLE} "
        "WHERE org_id = $1 AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'",
        org_id,
    )
    return (count or 0) < 10


async def export_user_data(pool: Any, subject_user_id: str, _org_id: str) -> dict:
    """
    Aggregate all user data across multiple tables.
    Called from worker — queries via pool.
    Returns dict of table → list of rows.
    """
    async with pool.acquire() as conn:
        data = {}

        # Core user record
        user_rows = await conn.fetch(
            'SELECT * FROM "03_iam".v_users WHERE id = $1',
            subject_user_id,
        )
        data["users"] = [dict(r) for r in user_rows]

        # User attributes (EAV)
        attrs = await conn.fetch(
            'SELECT * FROM "03_iam"."21_dtl_attrs" '
            "WHERE entity_type_id = 3 AND entity_id = $1",  # entity_type 3 = user
            subject_user_id,
        )
        data["attributes"] = [dict(r) for r in attrs]

        # Sessions
        sessions = await conn.fetch(
            'SELECT * FROM "03_iam"."16_fct_sessions" WHERE user_id = $1',
            subject_user_id,
        )
        data["sessions"] = [dict(r) for r in sessions]

        # Credentials (hashed, PII-minimal but keep for audit)
        creds = await conn.fetch(
            'SELECT id, user_id, kind_id, created_at FROM "03_iam"."11_fct_credentials" '
            "WHERE user_id = $1",
            subject_user_id,
        )
        data["credentials"] = [dict(r) for r in creds]

        # Org memberships
        memberships = await conn.fetch(
            'SELECT * FROM "03_iam"."40_lnk_org_members" WHERE user_id = $1',
            subject_user_id,
        )
        data["org_memberships"] = [dict(r) for r in memberships]

        # Role assignments
        role_assigns = await conn.fetch(
            'SELECT * FROM "03_iam"."41_lnk_role_assignments" WHERE user_id = $1',
            subject_user_id,
        )
        data["role_assignments"] = [dict(r) for r in role_assigns]

        # Audit events (user as actor)
        audit_events = await conn.fetch(
            'SELECT id, created_at, outcome, event_key, org_id FROM "04_audit"."60_evt_audit" '
            "WHERE actor_user_id = $1 LIMIT 10000",
            subject_user_id,
        )
        data["audit_events"] = [dict(r) for r in audit_events]

        return data


async def insert_dsar_payload(
    conn: Any,
    *,
    payload_id: str,
    job_id: str,
    ciphertext: bytes,
    nonce: bytes,
    dek_version: int,
    byte_size: int,
) -> str:
    """Insert an encrypted DSAR export payload row; returns the row id."""
    await conn.execute(
        f"INSERT INTO {_PAYLOADS_TABLE} "
        "(id, job_id, ciphertext, nonce, dek_version, byte_size) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        payload_id, job_id, ciphertext, nonce, dek_version, byte_size,
    )
    return payload_id


async def get_dsar_payload(conn: Any, job_id: str) -> dict | None:
    """Fetch the encrypted payload row for a job; returns dict with bytes fields or None."""
    row = await conn.fetchrow(
        f"SELECT id, job_id, ciphertext, nonce, dek_version, byte_size, created_at "
        f"FROM {_PAYLOADS_TABLE} WHERE job_id = $1",
        job_id,
    )
    return dict(row) if row else None


async def delete_user_data(conn: Any, subject_user_id: str, _org_id: str) -> dict[str, int]:
    """
    Cascade-delete all user data (hard delete except soft-delete user record).
    Returns dict of table → count of deleted rows.
    Called from worker.
    """
    counts = {}

    # Delete sessions
    c = await conn.execute(
        'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = $1',
        subject_user_id,
    )
    counts["sessions"] = int(c.split()[-1]) if "DELETE" in c else 0

    # Delete credentials
    c = await conn.execute(
        'DELETE FROM "03_iam"."11_fct_credentials" WHERE user_id = $1',
        subject_user_id,
    )
    counts["credentials"] = int(c.split()[-1]) if "DELETE" in c else 0

    # Delete org memberships
    c = await conn.execute(
        'DELETE FROM "03_iam"."40_lnk_org_members" WHERE user_id = $1',
        subject_user_id,
    )
    counts["org_memberships"] = int(c.split()[-1]) if "DELETE" in c else 0

    # Delete role assignments
    c = await conn.execute(
        'DELETE FROM "03_iam"."41_lnk_role_assignments" WHERE user_id = $1',
        subject_user_id,
    )
    counts["role_assignments"] = int(c.split()[-1]) if "DELETE" in c else 0

    # Delete EAV attributes
    c = await conn.execute(
        'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1 AND entity_type_id = 3',
        subject_user_id,
    )
    counts["attributes"] = int(c.split()[-1]) if "DELETE" in c else 0

    # Soft-delete user record (set deleted_at)
    await conn.execute(
        'UPDATE "03_iam"."10_fct_users" SET deleted_at = CURRENT_TIMESTAMP, '
        "updated_at = CURRENT_TIMESTAMP WHERE id = $1",
        subject_user_id,
    )
    counts["users"] = 1

    return counts
