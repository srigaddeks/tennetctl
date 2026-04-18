"""
authz — permission check primitive + AccessContext resolver.

require_permission(conn, user_id, scope_code, *, scope_org_id=None) -> None
    Raises AppError("FORBIDDEN") if the user lacks scope_code. Global scopes
    (scope_level='global') apply across all orgs. Org scopes require a
    matching scope_org_id on the active, non-expired, non-revoked user-role
    link.

resolve_access_context(conn, user_id, *, org_id=None, workspace_id=None)
    -> AccessContext
    Frozen dataclass with scope_codes and role_codes frozensets. Cached
    in-process for 5 min per (user_id, org_id, workspace_id).

invalidate_access_cache(user_id) — evict all entries for a user; call from
    any role or membership mutation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from importlib import import_module
from threading import Lock
from typing import Any

import asyncpg

_errors: Any = import_module("backend.01_core.errors")

# ---------------------------------------------------------------------------
# Schema constant
# ---------------------------------------------------------------------------

_IAM = '"03_iam"'

# ---------------------------------------------------------------------------
# In-process LRU cache — simple dict + TTL, good enough for v1.
# ---------------------------------------------------------------------------

_CACHE_TTL_SECS = 300  # 5 minutes

# {cache_key: (expires_at_monotonic, AccessContext)}
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

_PERMISSION_SQL = f"""
SELECT 1
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."44_lnk_role_scopes" rs ON rs.role_id = ur.role_id
JOIN {_IAM}."03_dim_scopes"      s  ON s.id = rs.scope_id
WHERE ur.user_id = $1
  AND s.code = $2
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND s.deprecated_at IS NULL
  AND (
      s.scope_level = 'global'
      OR (s.scope_level = 'org' AND ur.org_id = $3)
  )
LIMIT 1
"""

_PERMISSION_SQL_NO_ORG = f"""
SELECT 1
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."44_lnk_role_scopes" rs ON rs.role_id = ur.role_id
JOIN {_IAM}."03_dim_scopes"      s  ON s.id = rs.scope_id
WHERE ur.user_id = $1
  AND s.code = $2
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND s.deprecated_at IS NULL
  AND s.scope_level = 'global'
LIMIT 1
"""


async def require_permission(
    conn: asyncpg.Connection,
    user_id: str,
    scope_code: str,
    *,
    scope_org_id: str | None = None,
) -> None:
    """Assert user holds scope_code, raise FORBIDDEN if not.

    Args:
        conn: Active asyncpg connection (from pool.acquire() in route).
        user_id: UUID string of the user to check.
        scope_code: Scope code string, e.g. "flags:view:org".
        scope_org_id: Org UUID for org-level scopes. None = global only.

    Raises:
        AppError("FORBIDDEN", ..., 403) if the check fails.
    """
    if scope_org_id is not None:
        row = await conn.fetchrow(_PERMISSION_SQL, user_id, scope_code, scope_org_id)
    else:
        row = await conn.fetchrow(_PERMISSION_SQL_NO_ORG, user_id, scope_code)

    if not row:
        raise _errors.AppError(
            "FORBIDDEN",
            f"Permission required: {scope_code}",
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
    scope_codes: frozenset[str]
    role_codes: frozenset[str]


_SCOPES_ONLY_SQL = f"""
SELECT DISTINCT s.code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."44_lnk_role_scopes" rs ON rs.role_id = ur.role_id
JOIN {_IAM}."03_dim_scopes"      s  ON s.id = rs.scope_id
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND s.deprecated_at IS NULL
  AND (
      s.scope_level = 'global'
      OR ur.org_id = $2
  )
"""

_ROLE_CODES_SQL = f"""
SELECT DISTINCT a.key_text AS code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."21_dtl_attrs"       a     ON a.entity_id = ur.role_id
JOIN {_IAM}."20_dtl_attr_defs"   a_def ON a_def.id = a.attr_def_id
    AND a_def.entity_type_id = 4 AND a_def.code = 'code'
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND ur.org_id = $2
"""

_GLOBAL_SCOPES_SQL = f"""
SELECT DISTINCT s.code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."44_lnk_role_scopes" rs ON rs.role_id = ur.role_id
JOIN {_IAM}."03_dim_scopes"      s  ON s.id = rs.scope_id
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
  AND s.deprecated_at IS NULL
  AND s.scope_level = 'global'
"""

_GLOBAL_ROLE_CODES_SQL = f"""
SELECT DISTINCT a.key_text AS code
FROM {_IAM}."42_lnk_user_roles" ur
JOIN {_IAM}."21_dtl_attrs"       a     ON a.entity_id = ur.role_id
JOIN {_IAM}."20_dtl_attr_defs"   a_def ON a_def.id = a.attr_def_id
    AND a_def.entity_type_id = 4 AND a_def.code = 'code'
WHERE ur.user_id = $1
  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
  AND ur.revoked_at IS NULL
"""


async def resolve_access_context(
    conn: asyncpg.Connection,
    user_id: str,
    *,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> AccessContext:
    """Resolve a user's full access context for the given org.

    Returns a frozen AccessContext with scope_codes and role_codes populated.
    Results are cached in-process for 5 minutes per (user_id, org_id,
    workspace_id) triplet.

    Args:
        conn: Active asyncpg connection.
        user_id: UUID string of the requesting user.
        org_id: Org to resolve scopes against. None = global scopes only.
        workspace_id: Stored on the context but not used for scope filtering
                      (workspace-scoped auth is not yet in the schema).
    """
    cache_key = f"ac:{user_id}:{org_id or '_'}:{workspace_id or '_'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if org_id is not None:
        scope_rows = await conn.fetch(_SCOPES_ONLY_SQL, user_id, org_id)
        role_rows = await conn.fetch(_ROLE_CODES_SQL, user_id, org_id)
    else:
        scope_rows = await conn.fetch(_GLOBAL_SCOPES_SQL, user_id)
        role_rows = await conn.fetch(_GLOBAL_ROLE_CODES_SQL, user_id)

    ctx = AccessContext(
        user_id=user_id,
        org_id=org_id,
        workspace_id=workspace_id,
        scope_codes=frozenset(r["code"] for r in scope_rows),
        role_codes=frozenset(r["code"] for r in role_rows if r["code"] is not None),
    )
    _cache_set(cache_key, ctx)
    return ctx
