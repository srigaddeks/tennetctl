"""Service for capability catalog + role grants."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_authz: Any = import_module("backend.01_core.authz")

_repo: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.06_capabilities.repository"
)


async def get_catalog(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the full capability catalog: categories + actions + flags + permissions."""
    categories = await _repo.list_categories(conn)
    actions = await _repo.list_actions(conn)
    caps = await _repo.list_capabilities(conn)
    perms = await _repo.list_feature_permissions(conn)

    # Group permissions by flag_id.
    by_flag: dict[int, list[dict[str, Any]]] = {}
    for p in perms:
        by_flag.setdefault(p["flag_id"], []).append(p)

    capabilities = []
    for cap in caps:
        cap_with_perms = {**cap, "permissions": by_flag.get(cap["id"], [])}
        capabilities.append(cap_with_perms)

    return {
        "categories": categories,
        "actions": actions,
        "capabilities": capabilities,
    }


async def get_role_grants(
    conn: asyncpg.Connection, role_id: str
) -> dict[str, Any]:
    code = await _repo.get_role_code(conn, role_id)
    grants = await _repo.list_role_grants(conn, role_id)
    # Coerce created_at to str for Pydantic.
    for g in grants:
        g["created_at"] = g["created_at"].isoformat() if g.get("created_at") else ""
    return {"role_id": role_id, "role_code": code, "grants": grants}


async def grant_permissions(
    conn: asyncpg.Connection,
    *,
    role_id: str,
    permission_codes: list[str],
    actor_id: str,
) -> None:
    """Grant multiple feature_permissions to a role. Idempotent — no-op on duplicate."""
    for code in permission_codes:
        fp_id = await _repo.get_feature_permission_id_by_code(conn, code)
        if fp_id is None:
            raise _errors.AppError(
                "INVALID_PERMISSION", f"Unknown permission code: {code}", 400
            )
        await _repo.insert_grant(
            conn,
            grant_id=_core_id.uuid7(),
            role_id=role_id,
            feature_permission_id=fp_id,
            created_by=actor_id,
        )
    _authz.invalidate_access_cache(actor_id)


async def revoke_permission(
    conn: asyncpg.Connection,
    *,
    role_id: str,
    permission_code: str,
    actor_id: str,
) -> None:
    removed = await _repo.delete_grant_by_code(
        conn, role_id=role_id, permission_code=permission_code,
    )
    if removed == 0:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Grant not found: role={role_id} permission={permission_code}",
            404,
        )
    _authz.invalidate_access_cache(actor_id)
