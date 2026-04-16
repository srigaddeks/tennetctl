"""
featureflags.flags — service layer.

Validates scope/target combo + parent FK (via run_node iam.orgs.get /
iam.applications.get — keeps cross-sub-feature contact on the sanctioned path),
auto-provisions one fct_flag_states row per seeded environment on create,
cascades soft-delete on parent flag delete, emits audit on every mutation.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.01_flags.repository"
)

_AUDIT = "audit.events.emit"
_ORGS_GET = "iam.orgs.get"
_APPS_GET = "iam.applications.get"
_SENTINEL = object()


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_org(pool: Any, ctx: Any, org_id: str) -> None:
    result = await _catalog.run_node(pool, _ORGS_GET, ctx, {"id": org_id})
    if result.get("org") is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")


async def _assert_application(
    pool: Any, ctx: Any, application_id: str, expected_org_id: str,
) -> None:
    result = await _catalog.run_node(pool, _APPS_GET, ctx, {"id": application_id})
    app = result.get("application")
    if app is None:
        raise _errors.NotFoundError(f"Application {application_id!r} not found.")
    if app["org_id"] != expected_org_id:
        raise _errors.ValidationError(
            f"application {application_id!r} does not belong to org {expected_org_id!r}"
        )


async def create_flag(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    scope: str,
    org_id: str | None,
    application_id: str | None,
    flag_key: str,
    value_type: str,
    default_value: Any,
    description: str | None = None,
) -> dict:
    # Cross-sub-feature FK validations on sanctioned path.
    if scope == "org":
        await _assert_org(pool, ctx, org_id or "")
    elif scope == "application":
        await _assert_org(pool, ctx, org_id or "")
        await _assert_application(pool, ctx, application_id or "", org_id or "")

    # Dim resolution.
    scope_id = await _repo.get_scope_id(conn, scope)
    if scope_id is None:
        raise _errors.ValidationError(f"unknown scope {scope!r}")
    value_type_id = await _repo.get_value_type_id(conn, value_type)
    if value_type_id is None:
        raise _errors.ValidationError(f"unknown value_type {value_type!r}")

    # Uniqueness pre-check.
    existing = await _repo.get_flag_by_scope_key(
        conn,
        scope=scope,
        org_id=org_id,
        application_id=application_id,
        flag_key=flag_key,
    )
    if existing is not None:
        raise _errors.ConflictError(
            f"flag with key {flag_key!r} already exists at scope={scope}"
        )

    flag_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_flag(
            conn,
            id=flag_id,
            scope_id=scope_id,
            org_id=org_id,
            application_id=application_id,
            flag_key=flag_key,
            value_type_id=value_type_id,
            default_value=default_value,
            description=description,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"flag with key {flag_key!r} already exists"
        ) from e

    # Auto-provision per-env state rows (one per seeded env).
    env_ids = await _repo.list_env_ids(conn)
    for env_id in env_ids:
        await _repo.insert_flag_state(
            conn,
            id=_core_id.uuid7(),
            flag_id=flag_id,
            environment_id=env_id,
            created_by=created_by,
        )

    await _emit(
        pool, ctx,
        event_key="featureflags.flags.created",
        metadata={
            "flag_id": flag_id,
            "scope": scope,
            "flag_key": flag_key,
            "org_id": org_id,
            "application_id": application_id,
            "environments_provisioned": len(env_ids),
        },
    )

    created = await _repo.get_flag_by_id(conn, flag_id)
    if created is None:
        raise RuntimeError(f"flag {flag_id} not visible after insert")
    return created


async def get_flag(conn: Any, _ctx: Any, *, flag_id: str) -> dict | None:
    return await _repo.get_flag_by_id(conn, flag_id)


async def list_flags(
    conn: Any, _ctx: Any, *,
    limit: int = 50, offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    application_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_flags(
        conn,
        limit=limit, offset=offset,
        scope=scope, org_id=org_id, application_id=application_id,
        is_active=is_active,
    )


async def update_flag(
    pool: Any, conn: Any, ctx: Any, *,
    flag_id: str,
    default_value: Any = _SENTINEL,
    description: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
) -> dict:
    current = await _repo.get_flag_by_id(conn, flag_id)
    if current is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")

    changed: dict[str, object] = {}
    kw: dict[str, Any] = {"id": flag_id, "updated_by": ctx.user_id or "sys"}
    if default_value is not _SENTINEL and default_value != current["default_value"]:
        kw["default_value"] = default_value
        changed["default_value"] = default_value
    if description is not _SENTINEL and description != current.get("description"):
        kw["description"] = description
        changed["description"] = description
    if is_active is not _SENTINEL and is_active != current["is_active"]:
        kw["is_active"] = is_active
        changed["is_active"] = is_active

    if not changed:
        return current

    await _repo.update_flag_fields(conn, **kw)
    await _emit(
        pool, ctx,
        event_key="featureflags.flags.updated",
        metadata={"flag_id": flag_id, "changed": sorted(changed.keys())},
    )
    updated = await _repo.get_flag_by_id(conn, flag_id)
    if updated is None:
        raise RuntimeError(f"flag {flag_id} vanished after update")
    return updated


async def delete_flag(
    pool: Any, conn: Any, ctx: Any, *, flag_id: str,
) -> None:
    current = await _repo.get_flag_by_id(conn, flag_id)
    if current is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")
    updated_by = ctx.user_id or "sys"
    await _repo.soft_delete_flag_states_cascade(
        conn, flag_id=flag_id, updated_by=updated_by,
    )
    ok = await _repo.soft_delete_flag(conn, id=flag_id, updated_by=updated_by)
    if not ok:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="featureflags.flags.deleted",
        metadata={
            "flag_id": flag_id,
            "scope": current["scope"],
            "flag_key": current["flag_key"],
        },
    )


# ─── Flag states ────────────────────────────────────────────────────

async def get_flag_state(conn: Any, _ctx: Any, *, state_id: str) -> dict | None:
    return await _repo.get_flag_state_by_id(conn, state_id)


async def list_flag_states(
    conn: Any, _ctx: Any, *,
    limit: int = 50, offset: int = 0,
    flag_id: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_flag_states(
        conn, limit=limit, offset=offset, flag_id=flag_id,
    )


async def update_flag_state(
    pool: Any, conn: Any, ctx: Any, *,
    state_id: str,
    is_enabled: Any = _SENTINEL,
    env_default_value: Any = _SENTINEL,
) -> dict:
    current = await _repo.get_flag_state_by_id(conn, state_id)
    if current is None:
        raise _errors.NotFoundError(f"Flag state {state_id!r} not found.")

    changed: dict[str, object] = {}
    kw: dict[str, Any] = {"id": state_id, "updated_by": ctx.user_id or "sys"}
    if is_enabled is not _SENTINEL and is_enabled != current["is_enabled"]:
        kw["is_enabled"] = is_enabled
        changed["is_enabled"] = is_enabled
    if env_default_value is not _SENTINEL and env_default_value != current.get(
        "env_default_value"
    ):
        kw["env_default_value"] = env_default_value
        changed["env_default_value"] = env_default_value

    if not changed:
        return current

    await _repo.update_flag_state_fields(conn, **kw)
    await _emit(
        pool, ctx,
        event_key="featureflags.flags.state_updated",
        metadata={
            "state_id": state_id,
            "flag_id": current["flag_id"],
            "environment": current["environment"],
            "changed": sorted(changed.keys()),
        },
    )
    updated = await _repo.get_flag_state_by_id(conn, state_id)
    if updated is None:
        raise RuntimeError(f"flag state {state_id} vanished after update")
    return updated
