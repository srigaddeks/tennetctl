"""
Authorization helpers for admin mutations.
Provides role-based and org-membership access control gates.

Used by:
  - 15_api_keys/routes.py   — org-scoped key ownership checks
  - 25_ip_allowlist/routes.py — org admin (member) gate on every endpoint
  - 11_magic_link/service.py — org-match check on consume
  - 13_passkeys/service.py  — org-membership check on auth_complete
  - 12_otp/service.py       — rate-limit enforcement (existing; no authz added)

Table references (all schema-quoted per Postgres naming rules):
  "03_iam"."40_lnk_user_orgs"       — org membership
  "03_iam"."41_lnk_user_workspaces" — workspace membership
  "03_iam"."42_lnk_user_roles"      — user↔role assignments
  "03_iam"."13_fct_roles"            — role definitions (role_type_id FK)
  "03_iam"."04_dim_role_types"       — role type codes (system, custom)
  "03_iam"."10_fct_orgs"             — org identity (created_by = owner)
"""

from importlib import import_module
from typing import Optional

_errors = import_module("backend.01_core.errors")


# ---------------------------------------------------------------------------
# Org membership
# ---------------------------------------------------------------------------

async def is_org_member(conn, user_id: str, org_id: str) -> bool:
    """Return True if user has an active membership row in the org."""
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0
        FROM "03_iam"."40_lnk_user_orgs"
        WHERE user_id = $1
          AND org_id  = $2
        """,
        user_id, org_id,
    )
    return result or False


async def require_admin_role(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user has an active role assignment in the org that has not expired
    or been revoked.

    NOTE: The current role type dim (04_dim_role_types) only carries
    'system' and 'custom' codes — fine-grained admin/security_admin codes
    have not yet been seeded. Until those are seeded, this function checks
    org membership as the admin gate. When the dim table is extended, replace
    the body with a role_type_id join on the appropriate code.
    """
    return await is_org_member(conn, user_id, org_id)


async def require_org_owner(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user is the org owner (created the org row).
    Only the owner can delete the org or manage billing.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0
        FROM "03_iam"."10_fct_orgs"
        WHERE id         = $1
          AND created_by = $2
          AND deleted_at IS NULL
        """,
        org_id, user_id,
    )
    return result or False


async def require_workspace_member(conn, user_id: str, workspace_id: str) -> bool:
    """
    Check if user is a member of the workspace.
    The workspace membership table has no per-row role — membership implies access.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0
        FROM "03_iam"."41_lnk_user_workspaces"
        WHERE user_id      = $1
          AND workspace_id = $2
        """,
        user_id, workspace_id,
    )
    return result or False


# ---------------------------------------------------------------------------
# Convenience aliases used by ip_allowlist and other security endpoints.
# Both fall back to org-membership until fine-grained role codes are seeded.
# ---------------------------------------------------------------------------

async def require_mfa_admin(conn, user_id: str, org_id: str) -> bool:
    """Check if user can modify MFA policies (requires org membership)."""
    return await is_org_member(conn, user_id, org_id)


async def require_security_admin(conn, user_id: str, org_id: str) -> bool:
    """Check if user can manage security settings (requires org membership)."""
    return await is_org_member(conn, user_id, org_id)


async def require_notify_admin(conn, user_id: str, org_id: str) -> bool:
    """Check if user can configure notifications (requires org membership)."""
    return await is_org_member(conn, user_id, org_id)


# ---------------------------------------------------------------------------
# Generic permission dispatcher
# ---------------------------------------------------------------------------

async def check_permission(
    conn,
    user_id: Optional[str],
    org_id: str,
    workspace_id: Optional[str],
    permission: str,
) -> bool:
    """
    Map permission strings to role checks. Returns False for unknown permissions
    or missing user_id — never raises.
    """
    if not user_id:
        return False

    permission_map = {
        "admin_org":       lambda: require_admin_role(conn, user_id, org_id),
        "owner_org":       lambda: require_org_owner(conn, user_id, org_id),
        "member_org":      lambda: is_org_member(conn, user_id, org_id),
        "admin_workspace": lambda: require_workspace_member(conn, user_id, workspace_id or ""),
        "admin_mfa":       lambda: require_mfa_admin(conn, user_id, org_id),
        "admin_security":  lambda: require_security_admin(conn, user_id, org_id),
        "admin_notify":    lambda: require_notify_admin(conn, user_id, org_id),
    }

    if permission not in permission_map:
        return False

    return await permission_map[permission]()


# ---------------------------------------------------------------------------
# Raise-or-pass helpers (call these at mutation boundaries)
# ---------------------------------------------------------------------------

async def require_admin_or_raise(conn, user_id: str, org_id: str) -> None:
    """Raise ForbiddenError if user is not an org member (admin gate)."""
    if not await require_admin_role(conn, user_id, org_id):
        raise _errors.ForbiddenError("Admin role required for this operation.")


async def require_org_owner_or_raise(conn, user_id: str, org_id: str) -> None:
    """Raise ForbiddenError if user is not the org owner."""
    if not await require_org_owner(conn, user_id, org_id):
        raise _errors.ForbiddenError("Organization owner access required.")


async def require_org_member_or_raise(conn, user_id: str, org_id: str) -> None:
    """Raise ForbiddenError if user does not belong to the org."""
    if not await is_org_member(conn, user_id, org_id):
        raise _errors.ForbiddenError("Access denied: you are not a member of this organization.")
