"""Repository for monitoring.synthetic — raw SQL."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SELECT = """
    SELECT id, org_id, name, target_url, method, expected_status, timeout_ms,
           interval_seconds, headers, body, assertions, is_active,
           consecutive_failures, last_ok_at, last_fail_at, last_run_at,
           last_status_code, last_duration_ms, last_error,
           deleted_at, created_at, updated_at
      FROM "05_monitoring"."v_monitoring_synthetic_checks"
"""


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def insert(
    conn: Any,
    *,
    id: str,
    org_id: str,
    name: str,
    target_url: str,
    method: str,
    expected_status: int,
    timeout_ms: int,
    interval_seconds: int,
    headers: dict[str, Any],
    body: str | None,
    assertions: list[dict[str, Any]],
) -> dict[str, Any]:
    now = _now()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_synthetic_checks"
            (id, org_id, name, target_url, method, expected_status, timeout_ms,
             interval_seconds, headers, body, assertions, is_active,
             created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,TRUE,$12,$12)
        """,
        id, org_id, name, target_url, method, expected_status, timeout_ms,
        interval_seconds, headers, body, assertions, now,
    )
    row = await get_by_id(conn, id=id)
    assert row is not None
    return row


async def get_by_id(conn: Any, *, id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        _SELECT + " WHERE id = $1 AND deleted_at IS NULL",
        id,
    )
    return dict(row) if row else None


async def list_for_org(
    conn: Any,
    *,
    org_id: str,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    sql = _SELECT + " WHERE org_id = $1 AND deleted_at IS NULL"
    params: list[Any] = [org_id]
    if is_active is not None:
        params.append(is_active)
        sql += f" AND is_active = ${len(params)}"
    sql += " ORDER BY name"
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def list_all_active(conn: Any) -> list[dict[str, Any]]:
    """Runner query — all active checks across all orgs."""
    rows = await conn.fetch(
        _SELECT + " WHERE is_active = TRUE AND deleted_at IS NULL",
    )
    return [dict(r) for r in rows]


async def update(
    conn: Any,
    *,
    id: str,
    org_id: str,
    name: str | None,
    target_url: str | None,
    method: str | None,
    expected_status: int | None,
    timeout_ms: int | None,
    interval_seconds: int | None,
    headers: dict[str, Any] | None,
    body: str | None,
    assertions: list[dict[str, Any]] | None,
    is_active: bool | None,
) -> dict[str, Any] | None:
    sets: list[str] = []
    params: list[Any] = []

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if name is not None:         _add("name", name)
    if target_url is not None:   _add("target_url", target_url)
    if method is not None:       _add("method", method)
    if expected_status is not None: _add("expected_status", expected_status)
    if timeout_ms is not None:   _add("timeout_ms", timeout_ms)
    if interval_seconds is not None: _add("interval_seconds", interval_seconds)
    if headers is not None:      _add("headers", headers)
    if body is not None:         _add("body", body)
    if assertions is not None:   _add("assertions", assertions)
    if is_active is not None:    _add("is_active", is_active)

    if not sets:
        return await get_by_id(conn, id=id)

    params.append(_now())
    sets.append(f"updated_at = ${len(params)}")
    params.append(id)
    params.append(org_id)

    await conn.execute(
        f"""
        UPDATE "05_monitoring"."10_fct_monitoring_synthetic_checks"
           SET {', '.join(sets)}
         WHERE id = ${len(params) - 1}
           AND org_id = ${len(params)}
           AND deleted_at IS NULL
        """,
        *params,
    )
    return await get_by_id(conn, id=id)


async def soft_delete(conn: Any, *, id: str, org_id: str) -> bool:
    now = _now()
    result = await conn.execute(
        """
        UPDATE "05_monitoring"."10_fct_monitoring_synthetic_checks"
           SET deleted_at = $1, is_active = FALSE, updated_at = $1
         WHERE id = $2 AND org_id = $3 AND deleted_at IS NULL
        """,
        now, id, org_id,
    )
    return result.endswith(" 1")


async def upsert_state(
    conn: Any,
    *,
    check_id: str,
    consecutive_failures: int,
    last_ok_at: datetime | None,
    last_fail_at: datetime | None,
    last_run_at: datetime,
    last_status_code: int | None,
    last_duration_ms: int | None,
    last_error: str | None,
) -> None:
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."20_dtl_monitoring_synthetic_state"
            (check_id, consecutive_failures, last_ok_at, last_fail_at,
             last_run_at, last_status_code, last_duration_ms, last_error, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$5)
        ON CONFLICT (check_id) DO UPDATE SET
            consecutive_failures = EXCLUDED.consecutive_failures,
            last_ok_at           = EXCLUDED.last_ok_at,
            last_fail_at         = EXCLUDED.last_fail_at,
            last_run_at          = EXCLUDED.last_run_at,
            last_status_code     = EXCLUDED.last_status_code,
            last_duration_ms     = EXCLUDED.last_duration_ms,
            last_error           = EXCLUDED.last_error,
            updated_at           = EXCLUDED.last_run_at
        """,
        check_id, consecutive_failures, last_ok_at, last_fail_at,
        last_run_at, last_status_code, last_duration_ms, last_error,
    )
