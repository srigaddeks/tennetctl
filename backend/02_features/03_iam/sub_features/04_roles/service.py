"""iam.roles — service layer."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.repository"
)

_AUDIT = "audit.events.emit"
_ORGS_GET = "iam.orgs.get"


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_org_if_set(pool: Any, ctx: Any, org_id: str | None) -> None:
    if org_id is None:
        return
    result = await _catalog.run_node(pool, _ORGS_GET, ctx, {"id": org_id})
    if result.get("org") is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")


async def create_role(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str | None,
    role_type: str,
    code: str,
    label: str,
    description: str | None = None,
) -> dict:
    await _assert_org_if_set(pool, ctx, org_id)

    role_type_id = await _repo.get_role_type_id(conn, role_type)
    if role_type_id is None:
        raise _errors.ValidationError(
            f"unknown role_type {role_type!r}; must be 'system' or 'custom'",
        )

    existing = await _repo.get_by_org_code(conn, org_id, code)
    if existing is not None:
        scope_desc = "globally" if org_id is None else f"in org {org_id!r}"
        raise _errors.ConflictError(
            f"role with code {code!r} already exists {scope_desc}",
        )

    role_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_role(
            conn, id=role_id, org_id=org_id, role_type_id=role_type_id, created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"role with code {code!r} already exists",
        ) from e

    await _repo.set_attr(conn, role_id=role_id, attr_code="code", value=code, attr_row_id=_core_id.uuid7())
    await _repo.set_attr(conn, role_id=role_id, attr_code="label", value=label, attr_row_id=_core_id.uuid7())
    if description is not None:
        await _repo.set_attr(conn, role_id=role_id, attr_code="description", value=description, attr_row_id=_core_id.uuid7())

    await _emit(
        pool, ctx,
        event_key="iam.roles.created",
        metadata={"role_id": role_id, "org_id": org_id, "code": code, "role_type": role_type},
    )

    created = await _repo.get_by_id(conn, role_id)
    if created is None:
        raise RuntimeError(f"role {role_id} not visible after insert")
    return created


async def get_role(conn: Any, _ctx: Any, *, role_id: str) -> dict | None:
    return await _repo.get_by_id(conn, role_id)


async def list_roles(
    conn: Any, _ctx: Any, *,
    limit: int = 50, offset: int = 0,
    org_id: str | None = None,
    role_type: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_roles(
        conn, limit=limit, offset=offset,
        org_id=org_id, role_type=role_type, is_active=is_active,
    )


async def update_role(
    pool: Any, conn: Any, ctx: Any, *,
    role_id: str,
    label: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict:
    current = await _repo.get_by_id(conn, role_id)
    if current is None:
        raise _errors.NotFoundError(f"Role {role_id!r} not found.")

    changed: dict[str, object] = {}
    updated_by = ctx.user_id or "sys"
    any_attr = False

    for code, new_val in (("label", label), ("description", description)):
        if new_val is not None and new_val != current.get(code):
            await _repo.set_attr(
                conn, role_id=role_id, attr_code=code, value=new_val, attr_row_id=_core_id.uuid7(),
            )
            changed[code] = new_val
            any_attr = True

    if is_active is not None and is_active != current["is_active"]:
        ok = await _repo.update_active(conn, id=role_id, is_active=is_active, updated_by=updated_by)
        if not ok:
            raise _errors.NotFoundError(f"Role {role_id!r} not found.")
        changed["is_active"] = is_active

    if any_attr and "is_active" not in changed:
        await _repo.touch_role(conn, id=role_id, updated_by=updated_by)

    if not changed:
        return current

    await _emit(
        pool, ctx,
        event_key="iam.roles.updated",
        metadata={"role_id": role_id, "changed": sorted(changed.keys())},
    )

    updated = await _repo.get_by_id(conn, role_id)
    if updated is None:
        raise RuntimeError(f"role {role_id} vanished after update")
    return updated


async def delete_role(pool: Any, conn: Any, ctx: Any, *, role_id: str) -> None:
    ok = await _repo.soft_delete_role(conn, id=role_id, updated_by=(ctx.user_id or "sys"))
    if not ok:
        raise _errors.NotFoundError(f"Role {role_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="iam.roles.deleted",
        metadata={"role_id": role_id},
    )
