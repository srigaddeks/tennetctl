"""
Audit retention policy management and purge execution.
Phase: v0.1.8 Compliance
"""

import asyncpg
from uuid import UUID
from typing import Optional
from importlib import import_module

_id = import_module("backend.01_core.id")
_errors = import_module("backend.01_core.errors")


async def get_or_create_retention_policy(
    conn: asyncpg.Connection,
    org_id: UUID,
) -> dict:
    """Get retention policy for org, create default if missing."""
    policy = await conn.fetchrow(
        "SELECT * FROM 04_audit.fct_audit_retention_policies WHERE org_id = $1",
        org_id
    )
    if policy:
        return dict(policy)

    # Create default: 365 days, auto-purge disabled, exclude critical
    policy_id = _id.uuid7()
    await conn.execute(
        """
        INSERT INTO 04_audit.fct_audit_retention_policies
        (policy_id, org_id, retention_days, auto_purge_enabled, exclude_critical, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        policy_id, org_id, 365, False, True, (await conn.fetchval("SELECT MIN(user_id) FROM 03_iam.fct_users"))
    )
    return {
        "policy_id": policy_id,
        "org_id": org_id,
        "retention_days": 365,
        "auto_purge_enabled": False,
        "exclude_critical": True,
        "status": "active",
        "purge_count": 0,
    }


async def update_retention_policy(
    conn: asyncpg.Connection,
    policy_id: UUID,
    retention_days: Optional[int] = None,
    auto_purge_enabled: Optional[bool] = None,
    exclude_critical: Optional[bool] = None,
    status: Optional[str] = None,
) -> dict:
    """Update retention policy."""
    sets = []
    params = [policy_id]

    if retention_days is not None:
        sets.append(f"retention_days = ${len(params) + 1}")
        params.append(retention_days)
    if auto_purge_enabled is not None:
        sets.append(f"auto_purge_enabled = ${len(params) + 1}")
        params.append(auto_purge_enabled)
    if exclude_critical is not None:
        sets.append(f"exclude_critical = ${len(params) + 1}")
        params.append(exclude_critical)
    if status is not None:
        sets.append(f"status = ${len(params) + 1}")
        params.append(status)

    sets.append(f"updated_at = CURRENT_TIMESTAMP")

    if not sets:
        return await conn.fetchrow(
            "SELECT * FROM 04_audit.fct_audit_retention_policies WHERE policy_id = $1",
            policy_id
        )

    query = f"UPDATE 04_audit.fct_audit_retention_policies SET {', '.join(sets)} WHERE policy_id = $1 RETURNING *"
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else None


async def execute_purge_job(
    conn: asyncpg.Connection,
    policy_id: UUID,
    actor_id: UUID,
) -> dict:
    """
    Execute one-off purge for a policy.
    Hard-deletes audit events older than retention period.
    Returns job record.
    """
    job_id = _id.uuid7()

    # Create job record
    await conn.execute(
        """
        INSERT INTO 04_audit.evt_audit_purge_jobs
        (job_id, policy_id, status, created_by)
        VALUES ($1, $2, 'requested', $3)
        """,
        job_id, policy_id, actor_id
    )

    try:
        # Fetch policy
        policy = await conn.fetchrow(
            "SELECT * FROM 04_audit.fct_audit_retention_policies WHERE policy_id = $1",
            policy_id
        )
        if not policy:
            raise _errors.HTTPException(404, "Retention policy not found")

        # Mark job in progress
        await conn.execute(
            "UPDATE 04_audit.evt_audit_purge_jobs SET status = $1 WHERE job_id = $2",
            "in_progress", job_id
        )

        # Calculate cutoff date
        cutoff_date = f"CURRENT_TIMESTAMP - INTERVAL '{policy['retention_days']} days'"

        # Build WHERE clause
        where_clauses = [f"created_at < {cutoff_date}"]
        if policy["exclude_critical"]:
            where_clauses.append("category NOT IN ('security', 'compliance')")

        where_sql = " AND ".join(where_clauses)

        # Execute hard-delete
        result = await conn.execute(
            f"DELETE FROM 04_audit.evt_audit WHERE {where_sql}"
        )
        rows_purged = int(result.split()[-1]) if result else 0

        # Update job as completed
        await conn.execute(
            """
            UPDATE 04_audit.evt_audit_purge_jobs
            SET status = $1, rows_purged = $2, completed_at = CURRENT_TIMESTAMP
            WHERE job_id = $3
            """,
            "completed", rows_purged, job_id
        )

        # Update policy: increment count, set last_purge_at
        await conn.execute(
            """
            UPDATE 04_audit.fct_audit_retention_policies
            SET
                purge_count = purge_count + 1,
                last_purge_at = CURRENT_TIMESTAMP,
                next_purge_scheduled_at = CURRENT_TIMESTAMP + INTERVAL '1 day'
            WHERE policy_id = $1
            """,
            policy_id
        )

    except Exception as e:
        await conn.execute(
            """
            UPDATE 04_audit.evt_audit_purge_jobs
            SET status = $1, error_message = $2, completed_at = CURRENT_TIMESTAMP
            WHERE job_id = $3
            """,
            "failed", str(e), job_id
        )
        raise

    job = await conn.fetchrow(
        "SELECT * FROM 04_audit.evt_audit_purge_jobs WHERE job_id = $1",
        job_id
    )
    return dict(job) if job else None


async def get_retention_policy(
    pool: asyncpg.Pool,
    org_id: UUID,
) -> dict:
    """Retrieve retention policy for org."""
    async with pool.acquire() as conn:
        policy = await conn.fetchrow(
            "SELECT * FROM 04_audit.v_audit_retention_policies WHERE org_id = $1",
            org_id
        )
    return dict(policy) if policy else None


async def list_purge_jobs(
    pool: asyncpg.Pool,
    policy_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list, int]:
    """List purge jobs for a policy with pagination."""
    async with pool.acquire() as conn:
        jobs = await conn.fetch(
            """
            SELECT * FROM 04_audit.v_audit_purge_jobs
            WHERE policy_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            policy_id, limit, offset
        )
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM 04_audit.evt_audit_purge_jobs WHERE policy_id = $1",
            policy_id
        )
    return [dict(j) for j in jobs], total or 0
