"""Service layer for notify.template_variables."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_repo: Any = import_module("backend.02_features.06_notify.sub_features.04_variables.repository")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")
_errors: Any = import_module("backend.01_core.errors")


async def list_variables(conn: Any, *, template_id: str) -> list[dict]:
    return await _repo.list_variables(conn, template_id=template_id)


async def get_variable(conn: Any, *, var_id: str) -> dict | None:
    return await _repo.get_variable(conn, var_id=var_id)


async def create_variable(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    template_id: str,
    data: dict,
) -> dict:
    var_id = _core_id.uuid7()
    try:
        row = await _repo.create_variable(
            conn,
            var_id=var_id,
            template_id=template_id,
            name=data["name"],
            var_type=data["var_type"],
            static_value=data.get("static_value"),
            sql_template=data.get("sql_template"),
            param_bindings=data.get("param_bindings"),
            description=data.get("description"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"variable {data['name']!r} already exists for this template"
        ) from e
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "notify.variables.created",
            "outcome": "success",
            "metadata": {"var_id": var_id, "template_id": template_id, "name": data["name"]},
        },
    )
    return row


async def update_variable(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    var_id: str,
    data: dict,
) -> dict | None:
    row = await _repo.update_variable(conn, var_id=var_id, **data)
    if row:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "notify.variables.updated",
                "outcome": "success",
                "metadata": {"var_id": var_id},
            },
        )
    return row


async def delete_variable(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    var_id: str,
) -> bool:
    deleted = await _repo.delete_variable(conn, var_id=var_id)
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "notify.variables.deleted",
                "outcome": "success",
                "metadata": {"var_id": var_id},
            },
        )
    return deleted


async def resolve_variables(
    conn: Any,
    *,
    template_id: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve all registered variables for a template. No audit — read-only."""
    return await _repo.resolve_variables(conn, template_id=template_id, context=context)
