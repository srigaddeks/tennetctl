from __future__ import annotations

import asyncpg

from importlib import import_module

_errors_module = import_module("backend.01_core.errors")
_telemetry_module = import_module("backend.01_core.telemetry")
AuthorizationError = _errors_module.AuthorizationError
instrument_module_functions = _telemetry_module.instrument_module_functions

SCHEMA = '"03_auth_manage"'

# Org membership_type → system role code
_ORG_MEMBERSHIP_ROLE: dict[str, str] = {
    "owner":   "org_admin",
    "admin":   "org_admin",
    "member":  "org_member",
    "viewer":  "org_viewer",
    "billing": "org_viewer",
}

# Workspace membership_type → system role code
_WS_MEMBERSHIP_ROLE: dict[str, str] = {
    "owner":       "workspace_admin",
    "admin":       "workspace_admin",
    "contributor": "workspace_contributor",
    "viewer":      "workspace_viewer",
    "readonly":    "workspace_viewer",
}

# Build CASE expression for membership_type → role code
_ORG_CASE = " ".join(
    f"WHEN '{mtype}' THEN '{rcode}'"
    for mtype, rcode in _ORG_MEMBERSHIP_ROLE.items()
)
_WS_CASE = " ".join(
    f"WHEN '{mtype}' THEN '{rcode}'"
    for mtype, rcode in _WS_MEMBERSHIP_ROLE.items()
)


async def require_permission(
    connection: asyncpg.Connection,
    user_id: str,
    permission_code: str,
    *,
    scope_org_id: str | None = None,
    scope_workspace_id: str | None = None,
    api_key_scopes: tuple[str, ...] | None = None,
) -> None:
    """Assert the user holds a given permission code at the requested scope.

    Permission resolution (all branches are OR-ed via UNION ALL — first match wins):
      1. Platform groups   — groups with no org/workspace scope (super admin, platform roles)
      2. Scoped custom groups — user-defined groups scoped to this org/workspace
      3. Direct org membership → system role → permission
      4. Direct workspace membership → system role → permission
      5. GRC role on workspace membership → GRC role → permission

    System groups are NOT provisioned per org/workspace. Scoping is handled by
    the org/workspace membership tables directly (branches 3–5).

    Args:
        connection: Active asyncpg database connection.
        user_id: UUID of the user to check.
        permission_code: Feature permission code, e.g. 'orgs.manage', 'tasks.submit'.
        scope_org_id: Restrict check to this org (for org-scoped permissions).
        scope_workspace_id: Restrict check to this workspace (workspace-scoped permissions).
        api_key_scopes: Optional explicit scopes allowed by the API key.

    Raises:
        AuthorizationError: If the user does not hold the required permission.
    """
    if api_key_scopes is not None and permission_code not in api_key_scopes:
        raise AuthorizationError(f"API key does not include scope: {permission_code}")

    # Fixed args: $1=user_id, $2=permission_code
    # Variable args appended below, tracked with next_idx
    args: list = [user_id, permission_code]
    next_idx = 3  # next available $N placeholder

    branches: list[str] = []

    # ── Branch 1: Platform groups (no scope) ─────────────────────────────
    branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."18_lnk_group_memberships" gm
        JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gm.group_id
        JOIN {SCHEMA}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE gm.user_id = $1::UUID
          AND fp.code = $2
          AND gm.is_active = TRUE AND gm.is_deleted = FALSE
          AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
          AND gra.is_active = TRUE AND gra.is_deleted = FALSE
          AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND g.is_active = TRUE AND g.is_deleted = FALSE
          AND g.scope_org_id IS NULL AND g.scope_workspace_id IS NULL
    """)

    # ── Branch 2: Scoped custom groups ───────────────────────────────────
    if scope_workspace_id is not None:
        i_org = next_idx; next_idx += 1
        i_ws = next_idx; next_idx += 1
        args += [scope_org_id, scope_workspace_id]
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."18_lnk_group_memberships" gm
        JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gm.group_id
        JOIN {SCHEMA}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE gm.user_id = $1::UUID
          AND fp.code = $2
          AND gm.is_active = TRUE AND gm.is_deleted = FALSE
          AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
          AND gra.is_active = TRUE AND gra.is_deleted = FALSE
          AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND g.is_active = TRUE AND g.is_deleted = FALSE
          AND (
            (g.scope_org_id = ${i_org}::UUID AND g.scope_workspace_id IS NULL)
            OR g.scope_workspace_id = ${i_ws}::UUID
          )
        """)
    elif scope_org_id is not None:
        i_org = next_idx; next_idx += 1
        args.append(scope_org_id)
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."18_lnk_group_memberships" gm
        JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gm.group_id
        JOIN {SCHEMA}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE gm.user_id = $1::UUID
          AND fp.code = $2
          AND gm.is_active = TRUE AND gm.is_deleted = FALSE
          AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
          AND gra.is_active = TRUE AND gra.is_deleted = FALSE
          AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND g.is_active = TRUE AND g.is_deleted = FALSE
          AND g.scope_org_id = ${i_org}::UUID AND g.scope_workspace_id IS NULL
        """)

    # ── Branch 3: Direct org membership ──────────────────────────────────
    # i_org is always set by branch 2 before we reach here (both scope paths set it)
    if scope_org_id is not None:
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."31_lnk_org_memberships" om
        JOIN {SCHEMA}."16_fct_roles" r
          ON r.code = CASE om.membership_type {_ORG_CASE} ELSE NULL END
          AND r.is_deleted = FALSE
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = r.id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE om.user_id = $1::UUID
          AND om.org_id = ${i_org}::UUID
          AND om.is_active = TRUE AND om.is_deleted = FALSE
          AND (om.effective_to IS NULL OR om.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND fp.code = $2
        """)

    # ── Branches 4 & 5: Direct workspace membership ───────────────────────
    if scope_workspace_id is not None:
        # i_ws is already set from branch 2
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."36_lnk_workspace_memberships" wm
        JOIN {SCHEMA}."16_fct_roles" r
          ON r.code = CASE wm.membership_type {_WS_CASE} ELSE NULL END
          AND r.is_deleted = FALSE
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = r.id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE wm.user_id = $1::UUID
          AND wm.workspace_id = ${i_ws}::UUID
          AND wm.is_active = TRUE AND wm.is_deleted = FALSE
          AND (wm.effective_to IS NULL OR wm.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND fp.code = $2
        """)

        # GRC role on workspace membership
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."36_lnk_workspace_memberships" wm
        JOIN {SCHEMA}."16_fct_roles" r
          ON r.code = wm.grc_role_code
          AND r.is_deleted = FALSE
          AND r.role_level_code = 'workspace'
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = r.id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE wm.user_id = $1::UUID
          AND wm.workspace_id = ${i_ws}::UUID
          AND wm.grc_role_code IS NOT NULL
          AND wm.is_active = TRUE AND wm.is_deleted = FALSE
          AND (wm.effective_to IS NULL OR wm.effective_to > NOW())
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND fp.code = $2
        """)

    # ── Branch 6: Org-level GRC role assignments (47_lnk_grc_role_assignments)
    if scope_org_id is not None:
        branches.append(f"""
        SELECT 1
        FROM {SCHEMA}."47_lnk_grc_role_assignments" gra
        JOIN {SCHEMA}."16_fct_roles" r
          ON r.code = gra.grc_role_code
          AND r.is_deleted = FALSE
          AND r.role_level_code = 'workspace'
        JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = r.id
        JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
        WHERE gra.user_id = $1::UUID
          AND gra.org_id = ${i_org}::UUID
          AND gra.revoked_at IS NULL
          AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
          AND fp.code = $2
        """)

    union_sql = "\nUNION ALL\n".join(branches)
    row = await connection.fetchrow(
        f"SELECT EXISTS ({union_sql} LIMIT 1) AS granted",
        *args,
    )
    if not row or not row["granted"]:
        raise AuthorizationError(f"Permission required: {permission_code}")


instrument_module_functions(
    globals(),
    namespace="auth.permission_check",
    logger_name="backend.auth.permission.instrumentation",
)
