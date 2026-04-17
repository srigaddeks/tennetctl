"""
iam.gdpr — asyncpg repository.

Reads + writes "03_iam"."10_fct_gdpr_jobs".
dim_gdpr_kinds: export=1, erase=2
dim_gdpr_statuses: queued=1, processing=2, completed=3, failed=4, cancelled=5
"""

from __future__ import annotations

from typing import Any


_TABLE = '"03_iam"."10_fct_gdpr_jobs"'
_KINDS = '"03_iam"."01_dim_gdpr_kinds"'
_STATUSES = '"03_iam"."02_dim_gdpr_statuses"'


async def _kind_id(conn: Any, code: str) -> int:
    row = await conn.fetchrow(f"SELECT id FROM {_KINDS} WHERE code = $1", code)
    if row is None:
        raise RuntimeError(f"gdpr kind not found: {code}")
    return int(row["id"])


async def _status_id(conn: Any, code: str) -> int:
    row = await conn.fetchrow(f"SELECT id FROM {_STATUSES} WHERE code = $1", code)
    if row is None:
        raise RuntimeError(f"gdpr status not found: {code}")
    return int(row["id"])


async def insert_job(
    conn: Any,
    *,
    id: str,
    user_id: str,
    kind_code: str,
    status_code: str,
    hard_erase_at: Any = None,
    created_by: str,
) -> None:
    kind_id = await _kind_id(conn, kind_code)
    status_id = await _status_id(conn, status_code)
    await conn.execute(
        f"INSERT INTO {_TABLE} "
        "(id, user_id, kind_id, status_id, hard_erase_at, created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $6)",
        id, user_id, kind_id, status_id, hard_erase_at, created_by,
    )


async def get_job(conn: Any, job_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT j.id, j.user_id, k.code AS kind, s.code AS status, "
        "       j.requested_at, j.completed_at, j.hard_erase_at "
        f"FROM {_TABLE} j "
        f"JOIN {_KINDS} k ON k.id = j.kind_id "
        f"JOIN {_STATUSES} s ON s.id = j.status_id "
        "WHERE j.id = $1",
        job_id,
    )
    return dict(row) if row else None


async def get_latest_by_user_kind(conn: Any, user_id: str, kind_code: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT j.id, j.user_id, k.code AS kind, s.code AS status, "
        "       j.requested_at, j.completed_at, j.hard_erase_at "
        f"FROM {_TABLE} j "
        f"JOIN {_KINDS} k ON k.id = j.kind_id "
        f"JOIN {_STATUSES} s ON s.id = j.status_id "
        "WHERE j.user_id = $1 AND k.code = $2 "
        "ORDER BY j.requested_at DESC LIMIT 1",
        user_id, kind_code,
    )
    return dict(row) if row else None


async def update_job_status(
    conn: Any,
    *,
    job_id: str,
    status_code: str,
    download_url_hash: str | None = None,
    error_detail: str | None = None,
    updated_by: str,
) -> None:
    status_id = await _status_id(conn, status_code)
    await conn.execute(
        f"UPDATE {_TABLE} "
        "SET status_id = $1, "
        "    completed_at = CASE WHEN $2 IN ('completed','failed','cancelled') "
        "                       THEN CURRENT_TIMESTAMP ELSE completed_at END, "
        "    download_url_hash = COALESCE($3, download_url_hash), "
        "    error_detail = COALESCE($4, error_detail), "
        "    updated_by = $5, "
        "    updated_at = CURRENT_TIMESTAMP "
        "WHERE id = $6",
        status_id, status_code, download_url_hash, error_detail, updated_by, job_id,
    )


async def list_queued_exports(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT j.id, j.user_id "
        f"FROM {_TABLE} j "
        f"JOIN {_KINDS} k ON k.id = j.kind_id "
        f"JOIN {_STATUSES} s ON s.id = j.status_id "
        "WHERE k.code = 'export' AND s.code = 'queued' "
        "ORDER BY j.requested_at ASC LIMIT 10",
    )
    return [dict(r) for r in rows]


async def list_due_erasures(conn: Any) -> list[dict]:
    """Erase jobs where hard_erase_at has passed (still pending/processing)."""
    rows = await conn.fetch(
        f"SELECT j.id, j.user_id "
        f"FROM {_TABLE} j "
        f"JOIN {_KINDS} k ON k.id = j.kind_id "
        f"JOIN {_STATUSES} s ON s.id = j.status_id "
        "WHERE k.code = 'erase' AND s.code NOT IN ('completed','cancelled') "
        "  AND j.hard_erase_at <= CURRENT_TIMESTAMP "
        "ORDER BY j.hard_erase_at ASC LIMIT 10",
    )
    return [dict(r) for r in rows]
