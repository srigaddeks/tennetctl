"""Service layer for monitoring.synthetic — emits audit on mutations."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.repository"
)


async def create(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
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
    existing = await conn.fetchrow(
        """
        SELECT id FROM "05_monitoring"."10_fct_monitoring_synthetic_checks"
         WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL
        """,
        org_id, name,
    )
    if existing is not None:
        raise _errors.AppError(
            "DUPLICATE",
            f"synthetic check {name!r} already exists in this org",
            400,
        )
    check_id = _core_id.uuid7()
    row = await _repo.insert(
        conn,
        id=check_id, org_id=org_id, name=name, target_url=target_url,
        method=method, expected_status=expected_status,
        timeout_ms=timeout_ms, interval_seconds=interval_seconds,
        headers=headers, body=body, assertions=assertions,
    )
    await _emit_audit(
        pool, ctx, "monitoring.synthetic.created",
        {"check_id": check_id, "name": name, "target_url": target_url},
    )
    return row


async def list_checks(
    conn: Any, *, org_id: str, is_active: bool | None = None,
) -> list[dict[str, Any]]:
    return await _repo.list_for_org(conn, org_id=org_id, is_active=is_active)


async def get(conn: Any, *, org_id: str, id: str) -> dict[str, Any] | None:
    row = await _repo.get_by_id(conn, id=id)
    if row is None or row["org_id"] != org_id:
        return None
    return row


async def update(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    id: str,
    **fields: Any,
) -> dict[str, Any] | None:
    existing = await get(conn, org_id=org_id, id=id)
    if existing is None:
        return None
    row = await _repo.update(conn, id=id, org_id=org_id, **fields)
    await _emit_audit(
        pool, ctx, "monitoring.synthetic.updated",
        {"check_id": id, "fields": [k for k, v in fields.items() if v is not None]},
    )
    return row


async def delete(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    id: str,
) -> bool:
    ok = await _repo.soft_delete(conn, id=id, org_id=org_id)
    if ok:
        await _emit_audit(
            pool, ctx, "monitoring.synthetic.deleted",
            {"check_id": id},
        )
    return ok


async def _emit_audit(
    pool: Any, ctx: Any, event_key: str, metadata: dict[str, Any],
) -> None:
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": event_key, "outcome": "success", "metadata": metadata},
        )
    except Exception:  # noqa: BLE001
        pass
