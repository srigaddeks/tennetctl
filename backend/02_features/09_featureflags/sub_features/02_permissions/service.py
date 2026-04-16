"""
featureflags.permissions — service layer.

Owns both:
- CRUD on lnk_role_flag_permissions (grant / revoke / list)
- Shared `check_flag_permission(conn, ctx, flag_id, required)` used by 09-04/05/06

Permission resolution order:
1. If ctx.audit_category in ('setup', 'system') → allow (bootstrap / system calls).
2. If no ctx.user_id → deny.
3. If user has `flags:admin:all` IAM scope → allow.
4. Else compare max rank across user's role grants on this flag with required rank → allow if >=.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.02_permissions.repository"
)

_AUDIT = "audit.events.emit"

_RANK_BY_CODE = {"view": 1, "toggle": 2, "write": 3, "admin": 4}


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def check_flag_permission(
    conn: Any, ctx: Any, *, flag_id: str, required: str,
) -> None:
    """Raise ForbiddenError if caller lacks `required` permission on flag_id.

    `required` is one of: view / toggle / write / admin.
    """
    # Bootstrap bypass — system/setup calls always allowed.
    if ctx.audit_category in ("setup", "system"):
        return
    if ctx.user_id is None:
        raise _errors.ForbiddenError(
            f"user_id required to check flag permission ({required})"
        )
    # Global override
    if await _repo.user_has_admin_all_scope(conn, ctx.user_id):
        return
    needed_rank = _RANK_BY_CODE.get(required)
    if needed_rank is None:
        raise _errors.ValidationError(f"unknown required permission {required!r}")
    max_rank = await _repo.max_rank_for_user_on_flag(
        conn, user_id=ctx.user_id, flag_id=flag_id,
    )
    if max_rank < needed_rank:
        raise _errors.ForbiddenError(
            f"user lacks {required!r} permission on flag {flag_id!r} (has rank {max_rank})"
        )


async def grant_permission(
    pool: Any, conn: Any, ctx: Any, *,
    role_id: str, flag_id: str, permission: str,
) -> dict:
    # Validate flag exists via sanctioned cross-sub-feature path
    flag_result = await _catalog.run_node(
        pool, "featureflags.flags.get", ctx, {"id": flag_id},
    )
    if flag_result.get("flag") is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")
    # Validate permission code
    permission_id = await _repo.get_permission_id(conn, permission)
    if permission_id is None:
        raise _errors.ValidationError(f"unknown permission {permission!r}")
    # Validate role exists via run_node cross-sub-feature check
    role_result = await _catalog.run_node(pool, "iam.roles.get", ctx, {"id": role_id})
    if role_result.get("role") is None:
        raise _errors.NotFoundError(f"Role {role_id!r} not found.")

    existing = await _repo.get_by_triple(
        conn, role_id=role_id, flag_id=flag_id, permission_id=permission_id,
    )
    if existing is not None:
        raise _errors.ConflictError(
            f"role {role_id!r} already has {permission!r} on flag {flag_id!r}"
        )

    grant_id = _core_id.uuid7()
    try:
        await _repo.insert_grant(
            conn,
            id=grant_id,
            role_id=role_id,
            flag_id=flag_id,
            permission_id=permission_id,
            created_by=(ctx.user_id or "sys"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"role already has {permission!r} on this flag"
        ) from e

    await _emit(
        pool, ctx,
        event_key="featureflags.permissions.granted",
        metadata={
            "grant_id": grant_id,
            "role_id": role_id,
            "flag_id": flag_id,
            "permission": permission,
        },
    )
    created = await _repo.get_by_id(conn, grant_id)
    if created is None:
        raise RuntimeError(f"grant {grant_id} not visible after insert")
    return created


async def revoke_permission(
    pool: Any, conn: Any, ctx: Any, *, grant_id: str,
) -> None:
    existing = await _repo.get_by_id(conn, grant_id)
    if existing is None:
        raise _errors.NotFoundError(f"Grant {grant_id!r} not found.")
    ok = await _repo.delete_grant(conn, grant_id)
    if not ok:
        raise _errors.NotFoundError(f"Grant {grant_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="featureflags.permissions.revoked",
        metadata={
            "grant_id": grant_id,
            "role_id": existing["role_id"],
            "flag_id": existing["flag_id"],
            "permission": existing["permission"],
        },
    )


async def list_grants(
    conn: Any, _ctx: Any, *,
    limit: int = 100, offset: int = 0,
    role_id: str | None = None,
    flag_id: str | None = None,
    permission: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_grants(
        conn,
        limit=limit, offset=offset,
        role_id=role_id, flag_id=flag_id, permission=permission,
    )


async def get_grant(conn: Any, _ctx: Any, *, grant_id: str) -> dict | None:
    return await _repo.get_by_id(conn, grant_id)
