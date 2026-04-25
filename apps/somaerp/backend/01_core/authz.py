"""
Tiny RBAC helper for somaerp.

Checks whether the caller has a given permission code (e.g.
'somaerp_contacts.create'). The auth scope (org/workspace) is already
enforced by middleware; this layer adds role-based gating on top.

Implementation: somaerp shares Postgres with tennetctl, so we query
03_iam.42_lnk_user_roles ⨝ 09_featureflags.40_lnk_role_feature_permissions
directly. No HTTP roundtrip.

Bypass: users with role code 'platform_admin' always pass — they're
the org-level admin identity created at first-boot.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_errors = import_module("apps.somaerp.backend.01_core.errors")


_HAS_PERM_SQL = """
SELECT
    EXISTS (
        -- platform_admin bypass — independent of permission grants.
        SELECT 1
        FROM "03_iam"."42_lnk_user_roles" ur
        JOIN "03_iam"."21_dtl_attrs" a ON a.entity_id = ur.role_id
            AND a.attr_def_id = (
                SELECT id FROM "03_iam"."20_dtl_attr_defs"
                WHERE entity_type_id = 4 AND code = 'code' LIMIT 1
            )
        WHERE ur.user_id = $1
          AND a.key_text = 'platform_admin'
          AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
    )
    OR EXISTS (
        -- Permission granted via role assignment.
        SELECT 1
        FROM "03_iam"."42_lnk_user_roles" ur
        JOIN "09_featureflags"."40_lnk_role_feature_permissions" rfp
             ON rfp.role_id = ur.role_id
        JOIN "09_featureflags"."04_dim_feature_permissions" p
             ON p.id = rfp.feature_permission_id
        WHERE ur.user_id = $1
          AND p.code = $2
          AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
    );
"""


async def has_permission(conn: Any, *, user_id: str, perm_code: str) -> bool:
    """True if user has the permission directly OR has platform_admin role."""
    if not user_id:
        return False
    return bool(await conn.fetchval(_HAS_PERM_SQL, user_id, perm_code))


async def require_permission(
    pool: Any, *, user_id: str | None, perm_code: str,
) -> None:
    """Raises AuthError if user lacks the permission.

    Note: opens a fresh connection from the pool; safe to call from any
    layer. Cheap query (~1ms locally) — no caching needed for v1.
    """
    if not user_id:
        raise _errors.AuthError("Authentication required.")
    async with pool.acquire() as conn:
        ok = await has_permission(conn, user_id=user_id, perm_code=perm_code)
    if not ok:
        raise _errors.AuthError(
            f"Forbidden — missing permission '{perm_code}'.",
        )
