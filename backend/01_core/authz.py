"""
authz — permission check primitive + AccessContext resolver (phase 23R).

Permission codes are now `{flag_code}.{action_code}` pairs, resolved through
the unified capability catalog in schema "09_featureflags":

    lnk_user_roles → lnk_role_feature_permissions → dim_feature_permissions
        → dim_feature_flags (flag code) + dim_permission_actions (action code)

A role is a bundle of feature_permissions. Roles attach to users directly
(global via org_id IS NULL, or scoped via org_id = $).

require_permission(conn, user_id, "flag.action", *, scope_org_id=None)
    Raises AppError("FORBIDDEN") if the user lacks the permission. Global
    roles (ur.org_id IS NULL) match regardless of scope_org_id. Org-scoped
    roles require ur.org_id = scope_org_id.

resolve_access_context(conn, user_id, *, org_id=None, workspace_id=None)
    Returns a frozen AccessContext with permission_codes + role_codes.
    Cached in-process for 5 min per (user_id, org_id, workspace_id).

invalidate_access_cache(user_id) — evict all entries for a user; call from
    any role or grant mutation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from importlib import import_module
from threading import Lock
from typing import Any

import asyncpg

_errors: Any = import_module("backend.01_core.errors")

_IAM = '"03_iam"'
_FF = '"09_featureflags"'

# ---------------------------------------------------------------------------
# In-process LRU cache — simple dict + TTL.
# ---------------------------------------------------------------------------

_CACHE_TTL_SECS = 300  # 5 minutes

_cache: dict[str, tuple[float, "AccessContext"]] = {}
_cache_lock = Lock()


def _cache_get(key: str) -> "AccessContext | None":
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del _cache[key]
            return None
        return value


def _cache_set(key: str, value: "AccessContext") -> None:
    with _cache_lock:
        _cache[key] = (time.monotonic() + _CACHE_TTL_SECS, value)


def invalidate_access_cache(user_id: str) -> None:
    """Evict all cached AccessContext entries for the given user."""
    prefix = f"ac:{user_id}:"
    with _cache_lock:
        for key in [k for k in _cache if k.startswith(prefix)]:
            _cache.pop(key, None)


# ---------------------------------------------------------------------------
# require_permission
# ---------------------------------------------------------------------------

_PERMISSION_SQL_WITH_ORG = f"""
SELECT 1
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_FF}."40_lnk_role_feature_permissions" rfp ON rfp.role_id = ur.role_id
JOIN {_FF}."04_dim_feature_permissions" fp        ON fp.id = rfp.feature_permission_id
WHERE ur.user_id = $1
  AND fp.code = $2
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND fp.deprecated_at IS NULL
  AND (ur.org_id IS NULL OR ur.org_id = $3)
LIMIT 1
"""

_PERMISSION_SQL_NO_ORG = f"""
SELECT 1
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_FF}."40_lnk_role_feature_permissions" rfp ON rfp.role_id = ur.role_id
JOIN {_FF}."04_dim_feature_permissions" fp        ON fp.id = rfp.feature_permission_id
WHERE ur.user_id = $1
  AND fp.code = $2
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND fp.deprecated_at IS NULL
  AND ur.org_id IS NULL
LIMIT 1
"""


async def require_permission(
    conn: asyncpg.Connection,
    user_id: str,
    permission_code: str,
    *,
    scope_org_id: str | None = None,
) -> None:
    """Assert user holds permission_code, raise FORBIDDEN if not.

    Args:
        conn: Active asyncpg connection (from pool.acquire() in route).
        user_id: UUID string of the user to check.
        permission_code: "flag.action" (e.g. "vault_secrets.view", "orgs.update").
        scope_org_id: Org UUID. When set, org-scoped roles matching this org
            satisfy the check in addition to global roles. When None, only
            global roles count.

    Raises:
        AppError("FORBIDDEN", ..., 403) if the check fails.
    """
    if scope_org_id is not None:
        row = await conn.fetchrow(
            _PERMISSION_SQL_WITH_ORG, user_id, permission_code, scope_org_id,
        )
    else:
        row = await conn.fetchrow(
            _PERMISSION_SQL_NO_ORG, user_id, permission_code,
        )

    if not row:
        raise _errors.AppError(
            "FORBIDDEN",
            f"Permission required: {permission_code}",
            403,
        )


# ---------------------------------------------------------------------------
# AccessContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AccessContext:
    """Immutable bundle of resolved access state for a single request."""

    user_id: str
    org_id: str | None
    workspace_id: str | None
    permission_codes: frozenset[str]
    role_codes: frozenset[str]

    # Back-compat alias — older code refers to `scope_codes`. Same data now
    # represents the "flag.action" permission set.
    @property
    def scope_codes(self) -> frozenset[str]:
        return self.permission_codes


_PERMISSIONS_WITH_ORG_SQL = f"""
SELECT DISTINCT fp.code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_FF}."40_lnk_role_feature_permissions" rfp ON rfp.role_id = ur.role_id
JOIN {_FF}."04_dim_feature_permissions" fp        ON fp.id = rfp.feature_permission_id
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND fp.deprecated_at IS NULL
  AND (ur.org_id IS NULL OR ur.org_id = $2)
"""

_PERMISSIONS_GLOBAL_ONLY_SQL = f"""
SELECT DISTINCT fp.code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_FF}."40_lnk_role_feature_permissions" rfp ON rfp.role_id = ur.role_id
JOIN {_FF}."04_dim_feature_permissions" fp        ON fp.id = rfp.feature_permission_id
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND fp.deprecated_at IS NULL
  AND ur.org_id IS NULL
"""

_ROLE_CODES_WITH_ORG_SQL = f"""
SELECT DISTINCT a.key_text AS code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."21_dtl_attrs"       a     ON a.entity_id = ur.role_id
JOIN {_IAM}."20_dtl_attr_defs"   a_def ON a_def.id = a.attr_def_id
    AND a_def.entity_type_id = 4 AND a_def.code = 'code'
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND (ur.org_id IS NULL OR ur.org_id = $2)
"""

_ROLE_CODES_GLOBAL_ONLY_SQL = f"""
SELECT DISTINCT a.key_text AS code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."21_dtl_attrs"       a     ON a.entity_id = ur.role_id
JOIN {_IAM}."20_dtl_attr_defs"   a_def ON a_def.id = a.attr_def_id
    AND a_def.entity_type_id = 4 AND a_def.code = 'code'
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND ur.org_id IS NULL
"""


async def resolve_access_context(
    conn: asyncpg.Connection,
    user_id: str,
    *,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> AccessContext:
    """Resolve a user's full access context for the given org.

    Returns a frozen AccessContext with `permission_codes` (set of
    "flag.action" strings) and `role_codes`. Cached in-process for 5
    minutes per (user_id, org_id, workspace_id).

    Args:
        conn: Active asyncpg connection.
        user_id: UUID string of the requesting user.
        org_id: Org to resolve against. None = global-role permissions only.
        workspace_id: Stored but not used for filtering (workspace-scoped
            roles go via `fct_roles.scope_workspace_id` if/when added;
            currently not queried).
    """
    cache_key = f"ac:{user_id}:{org_id or '_'}:{workspace_id or '_'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if org_id is not None:
        perm_rows = await conn.fetch(_PERMISSIONS_WITH_ORG_SQL, user_id, org_id)
        role_rows = await conn.fetch(_ROLE_CODES_WITH_ORG_SQL, user_id, org_id)
    else:
        perm_rows = await conn.fetch(_PERMISSIONS_GLOBAL_ONLY_SQL, user_id)
        role_rows = await conn.fetch(_ROLE_CODES_GLOBAL_ONLY_SQL, user_id)

    ctx = AccessContext(
        user_id=user_id,
        org_id=org_id,
        workspace_id=workspace_id,
        permission_codes=frozenset(r["code"] for r in perm_rows),
        role_codes=frozenset(r["code"] for r in role_rows if r["code"] is not None),
    )
    _cache_set(cache_key, ctx)
    return ctx
