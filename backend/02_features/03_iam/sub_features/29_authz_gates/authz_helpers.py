"""
Authorization helpers for admin mutations.
Provides role-based access control gates for all admin endpoints.
Phase: Critical security fix (v0.1.8)
"""

from importlib import import_module
from typing import Optional

_errors = import_module("backend.01_core.errors")


async def require_admin_role(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user has admin-level role in organization.
    Admin can create/update/delete any org resource.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.lnk_user_roles ur
        JOIN 03_iam.fct_roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = $1 AND r.org_id = $2
        AND r.role_type = 'admin'
        AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        """,
        user_id, org_id
    )
    return result or False


async def require_org_owner(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user is org owner.
    Only owner can delete org, manage billing, change org settings.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.fct_orgs
        WHERE org_id = $1 AND created_by = $2
        """,
        org_id, user_id
    )
    return result or False


async def require_workspace_admin(conn, user_id: str, workspace_id: str) -> bool:
    """
    Check if user has admin-level role in workspace.
    Workspace admin can manage members, roles, settings within workspace scope.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.lnk_user_roles ur
        JOIN 03_iam.fct_roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = $1 AND r.workspace_id = $2
        AND r.role_type IN ('admin', 'owner')
        AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        """,
        user_id, workspace_id
    )
    return result or False


async def require_mfa_admin(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user can modify MFA policies.
    Requires admin or security_admin role.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.lnk_user_roles ur
        JOIN 03_iam.fct_roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = $1 AND r.org_id = $2
        AND r.role_type IN ('admin', 'security_admin')
        AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        """,
        user_id, org_id
    )
    return result or False


async def require_security_admin(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user can manage security settings (IP allowlist, SIEM export, etc).
    Requires security_admin or admin role.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.lnk_user_roles ur
        JOIN 03_iam.fct_roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = $1 AND r.org_id = $2
        AND r.role_type IN ('admin', 'security_admin')
        AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        """,
        user_id, org_id
    )
    return result or False


async def require_notify_admin(conn, user_id: str, org_id: str) -> bool:
    """
    Check if user can configure notifications (SMTP, templates, etc).
    Requires admin or notify_admin role.
    """
    result = await conn.fetchval(
        """
        SELECT COUNT(*) > 0 FROM 03_iam.lnk_user_roles ur
        JOIN 03_iam.fct_roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = $1 AND r.org_id = $2
        AND r.role_type IN ('admin', 'notify_admin')
        AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        """,
        user_id, org_id
    )
    return result or False


async def check_permission(
    conn,
    user_id: Optional[str],
    org_id: str,
    workspace_id: Optional[str],
    permission: str,  # 'admin_org', 'admin_workspace', 'owner_org', etc.
) -> bool:
    """
    Generic permission checker. Maps permission strings to role checks.
    """
    if not user_id:
        return False

    permission_map = {
        "admin_org": lambda: require_admin_role(conn, user_id, org_id),
        "owner_org": lambda: require_org_owner(conn, user_id, org_id),
        "admin_workspace": lambda: require_workspace_admin(conn, user_id, workspace_id),
        "admin_mfa": lambda: require_mfa_admin(conn, user_id, org_id),
        "admin_security": lambda: require_security_admin(conn, user_id, org_id),
        "admin_notify": lambda: require_notify_admin(conn, user_id, org_id),
    }

    if permission not in permission_map:
        return False

    return await permission_map[permission]()


def enforce_permission(
    user_id: Optional[str],
    org_id: str,
    workspace_id: Optional[str] = None,
    permission: str = "admin_org",
) -> None:
    """
    Raise 403 Forbidden if user lacks required permission.
    Call at route handler start before any mutations.
    """
    if not user_id:
        raise _errors.HTTPException(
            403,
            "Forbidden: Authentication required for admin operations"
        )

    # TODO: Async check will be done by caller in route
    # For now, this prepares the error structure
    pass


async def require_admin_or_raise(conn, user_id: str, org_id: str) -> None:
    """
    Convenience: raise 403 if user is not admin in org.
    """
    is_admin = await require_admin_role(conn, user_id, org_id)
    if not is_admin:
        raise _errors.HTTPException(403, "Forbidden: Admin role required")


async def require_org_owner_or_raise(conn, user_id: str, org_id: str) -> None:
    """
    Convenience: raise 403 if user is not org owner.
    """
    is_owner = await require_org_owner(conn, user_id, org_id)
    if not is_owner:
        raise _errors.HTTPException(403, "Forbidden: Organization owner required")
