"""iam.applications — service layer. Org-scoped, per-org code uniqueness."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.06_applications.repository"
)

_AUDIT = "audit.events.emit"
_ORGS_GET = "iam.orgs.get"


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_org(pool: Any, ctx: Any, org_id: str) -> None:
    result = await _catalog.run_node(pool, _ORGS_GET, ctx, {"id": org_id})
    if result.get("org") is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")


async def create_application(
    pool: Any, conn: Any, ctx: Any, *,
    org_id: str, code: str, label: str, description: str | None = None,
) -> dict:
    await _assert_org(pool, ctx, org_id)

    if await _repo.get_by_org_code(conn, org_id, code) is not None:
        raise _errors.ConflictError(
            f"application with code {code!r} already exists in org {org_id!r}",
        )

    app_id = _core_id.uuid7()
    try:
        await _repo.insert_application(
            conn, id=app_id, org_id=org_id, created_by=(ctx.user_id or "sys"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"application with code {code!r} already exists in org {org_id!r}",
        ) from e

    await _repo.set_attr(conn, application_id=app_id, attr_code="code", value=code, attr_row_id=_core_id.uuid7())
    await _repo.set_attr(conn, application_id=app_id, attr_code="label", value=label, attr_row_id=_core_id.uuid7())
    if description is not None:
        await _repo.set_attr(conn, application_id=app_id, attr_code="description", value=description, attr_row_id=_core_id.uuid7())

    await _emit(
        pool, ctx,
        event_key="iam.applications.created",
        metadata={"application_id": app_id, "org_id": org_id, "code": code},
    )
    created = await _repo.get_by_id(conn, app_id)
    if created is None:
        raise RuntimeError(f"application {app_id} not visible after insert")
    return created


async def get_application(conn: Any, _ctx: Any, *, application_id: str) -> dict | None:
    row = await _repo.get_by_id(conn, application_id)
    if row is None:
        return None
    row["scope_ids"] = await _repo.list_scope_ids(conn, application_id)
    return row


async def list_applications(
    conn: Any, _ctx: Any, *,
    limit: int = 50, offset: int = 0,
    org_id: str | None = None, is_active: bool | None = None,
    code: str | None = None,
) -> tuple[list[dict], int]:
    items, total = await _repo.list_applications(
        conn, limit=limit, offset=offset, org_id=org_id,
        is_active=is_active, code=code,
    )
    if items:
        scopes = await _repo.list_scope_ids_many(conn, [r["id"] for r in items])
        for r in items:
            r["scope_ids"] = scopes.get(r["id"], [])
    return items, total


async def update_application(
    pool: Any, conn: Any, ctx: Any, *,
    application_id: str,
    label: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    scope_ids: list[int] | None = None,
) -> dict:
    current = await _repo.get_by_id(conn, application_id)
    if current is None:
        raise _errors.NotFoundError(f"Application {application_id!r} not found.")

    changed: dict[str, object] = {}
    updated_by = ctx.user_id or "sys"
    any_attr = False
    for code, new_val in (("label", label), ("description", description)):
        if new_val is not None and new_val != current.get(code):
            await _repo.set_attr(
                conn, application_id=application_id, attr_code=code, value=new_val, attr_row_id=_core_id.uuid7(),
            )
            changed[code] = new_val
            any_attr = True
    if is_active is not None and is_active != current["is_active"]:
        ok = await _repo.update_active(conn, id=application_id, is_active=is_active, updated_by=updated_by)
        if not ok:
            raise _errors.NotFoundError(f"Application {application_id!r} not found.")
        changed["is_active"] = is_active

    if scope_ids is not None:
        requested = sorted(set(scope_ids))
        if requested:
            found = await _repo.dim_scope_ids_exist(conn, requested)
            missing = [s for s in requested if s not in found]
            if missing:
                raise _errors.ValidationError(
                    f"unknown scope ids: {missing}",
                )
        previous = await _repo.list_scope_ids(conn, application_id)
        if previous != requested:
            await _repo.replace_application_scopes(
                conn,
                application_id=application_id,
                org_id=current["org_id"],
                scope_ids=requested,
                created_by=updated_by,
            )
            changed["scope_ids"] = requested

    if any_attr and "is_active" not in changed:
        await _repo.touch_application(conn, id=application_id, updated_by=updated_by)

    if not changed:
        current["scope_ids"] = await _repo.list_scope_ids(conn, application_id)
        return current

    await _emit(
        pool, ctx,
        event_key="iam.applications.updated",
        metadata={"application_id": application_id, "changed": sorted(changed.keys())},
    )
    updated = await _repo.get_by_id(conn, application_id)
    if updated is None:
        raise RuntimeError(f"application {application_id} vanished after update")
    updated["scope_ids"] = await _repo.list_scope_ids(conn, application_id)
    return updated


async def delete_application(pool: Any, conn: Any, ctx: Any, *, application_id: str) -> None:
    ok = await _repo.soft_delete_application(conn, id=application_id, updated_by=(ctx.user_id or "sys"))
    if not ok:
        raise _errors.NotFoundError(f"Application {application_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="iam.applications.deleted",
        metadata={"application_id": application_id},
    )
