"""Service layer for monitoring.saved_queries."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.repository"
)
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")

_logs_svc: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.service"
)
_metrics_svc: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)
_traces_svc: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.service"
)


def _validate_dsl(target: str, dsl: dict[str, Any]) -> None:
    try:
        if target == "logs":
            _dsl.validate_logs_query(dsl)
        elif target == "metrics":
            _dsl.validate_metrics_query(dsl)
        elif target == "traces":
            _dsl.validate_traces_query(dsl)
        else:
            raise _errors.ValidationError(f"unknown target {target!r}")
    except _dsl.InvalidQueryError as e:
        raise _errors.ValidationError(f"invalid DSL: {e}") from e


async def create(
    conn: Any,
    *,
    org_id: str,
    owner_user_id: str,
    name: str,
    description: str | None,
    target: str,
    dsl: dict[str, Any],
    shared: bool,
) -> dict[str, Any]:
    _validate_dsl(target, dsl)
    sq_id = _core_id.uuid7()
    return await _repo.insert(
        conn,
        id=sq_id, org_id=org_id, owner_user_id=owner_user_id,
        name=name, description=description, target=target,
        dsl=dsl, shared=shared,
    )


async def list_for_user(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    target: str | None = None,
) -> list[dict[str, Any]]:
    return await _repo.list_for_user(conn, org_id=org_id, user_id=user_id, target=target)


async def get(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
) -> dict[str, Any] | None:
    row = await _repo.get_by_id(conn, id=id)
    if row is None:
        return None
    # Authorization: caller must be owner OR in same org and row.shared=true.
    if row["org_id"] != org_id:
        return None
    if row["owner_user_id"] != user_id and not row["shared"]:
        return None
    return row


async def update(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
    name: str | None,
    description: str | None,
    dsl: dict[str, Any] | None,
    shared: bool | None,
    is_active: bool | None,
) -> dict[str, Any] | None:
    existing = await _repo.get_by_id(conn, id=id)
    if existing is None or existing["org_id"] != org_id:
        return None
    if existing["owner_user_id"] != user_id:
        raise _errors.ForbiddenError("only the owner may update this saved query")
    if dsl is not None:
        _validate_dsl(existing["target"], dsl)
    return await _repo.update(
        conn, id=id, name=name, description=description,
        dsl=dsl, shared=shared, is_active=is_active,
    )


async def delete(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
) -> bool:
    existing = await _repo.get_by_id(conn, id=id)
    if existing is None or existing["org_id"] != org_id:
        return False
    if existing["owner_user_id"] != user_id:
        raise _errors.ForbiddenError("only the owner may delete this saved query")
    return await _repo.soft_delete(conn, id=id)


async def run(
    conn: Any,
    ctx: Any,
    *,
    id: str,
) -> dict[str, Any]:
    org_id = getattr(ctx, "org_id", None)
    user_id = getattr(ctx, "user_id", None) or ""
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "ctx.org_id required", 401)
    row = await get(conn, org_id=org_id, user_id=user_id, id=id)
    if row is None:
        raise _errors.NotFoundError(f"saved query {id!r} not found")
    import json as _json
    dsl_body = row["dsl"]
    if isinstance(dsl_body, str):
        dsl_body = _json.loads(dsl_body)
    target = row["target"]
    if target == "logs":
        items, next_cursor = await _logs_svc.query(conn, ctx, dsl_body)
    elif target == "metrics":
        items, next_cursor = await _metrics_svc.query(conn, ctx, dsl_body)
    elif target == "traces":
        items, next_cursor = await _traces_svc.query(conn, ctx, dsl_body)
    else:
        raise _errors.ValidationError(f"unknown target {target!r}")
    return {"target": target, "items": items, "next_cursor": next_cursor}
