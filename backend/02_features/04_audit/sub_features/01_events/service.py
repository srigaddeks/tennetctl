"""
audit.events — service layer (read path).

Pure read-path — never emits audit itself. HTTP-layer audit (e.g. "who queried
the audit log") is emitted at the route via run_node("audit.events.emit", ...)
following the vault precedent (HTTP reads audit, node reads don't).

Authorization (v1): if a caller provides a non-matching org_id filter, the
service returns the filters unchanged — the HTTP layer is responsible for
rejecting cross-org requests via the fail-closed filter-override helper.
This keeps service-layer reads composable for admin surfaces that legitimately
cross orgs.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.repository"
)


async def query(
    conn: Any,
    _ctx: Any,
    *,
    filters: dict[str, Any],
    cursor: str | None,
    limit: int,
) -> tuple[list[dict], str | None]:
    return await _repo.list_events(conn, filters=filters, cursor=cursor, limit=limit)


async def get(conn: Any, _ctx: Any, *, event_id: str) -> dict | None:
    return await _repo.get_event(conn, event_id)


async def stats(
    conn: Any,
    _ctx: Any,
    *,
    filters: dict[str, Any],
    bucket: str,
) -> dict:
    return await _repo.stats(conn, filters=filters, bucket=bucket)


async def list_keys(conn: Any) -> tuple[list[dict], int]:
    return await _repo.list_event_keys(conn)


async def upsert_key(
    conn: Any,
    *,
    key: str,
    label: str,
    description: str | None,
    category_code: str,
) -> None:
    await _repo.upsert_event_key(
        conn, key=key, label=label, description=description, category_code=category_code,
    )


async def funnel(
    conn: Any,
    *,
    steps: list[str],
    org_id: str | None,
    since: Any,
    until: Any,
) -> list[dict]:
    return await _repo.funnel_analysis(conn, steps=steps, org_id=org_id, since=since, until=until)


async def retention(
    conn: Any,
    *,
    anchor: str,
    return_event: str,
    org_id: str | None,
    bucket: str,
    periods: int,
) -> dict:
    return await _repo.retention_analysis(
        conn, anchor=anchor, return_event=return_event, org_id=org_id, bucket=bucket, periods=periods,
    )
