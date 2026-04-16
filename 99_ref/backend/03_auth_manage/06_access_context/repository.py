from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import OrgInfo, UserAccessAction, WorkspaceInfo

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_ACCESS_COLS = """
    ff.code  AS feature_code,
    ff.name  AS feature_name,
    pa.code  AS action_code,
    cat.code AS category_code,
    ff.access_mode,
    ff.env_dev,
    ff.env_staging,
    ff.env_prod
"""

_ACTIVE_FILTERS = """
    gm.is_active = TRUE AND gm.is_deleted = FALSE
    AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
    AND g.is_active = TRUE AND g.is_deleted = FALSE
    AND gra.is_active = TRUE AND gra.is_deleted = FALSE
    AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
    AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
"""

_ORG_MEMBERSHIP_ROLE: dict[str, str] = {
    "owner": "org_admin",
    "admin": "org_admin",
    "member": "org_member",
    "viewer": "org_viewer",
    "billing": "org_viewer",
}

_WS_MEMBERSHIP_ROLE: dict[str, str] = {
    "owner": "workspace_admin",
    "admin": "workspace_admin",
    "contributor": "workspace_contributor",
    "viewer": "workspace_viewer",
    "readonly": "workspace_viewer",
}

_ORG_CASE = " ".join(
    f"WHEN '{membership_type}' THEN '{role_code}'"
    for membership_type, role_code in _ORG_MEMBERSHIP_ROLE.items()
)
_WS_CASE = " ".join(
    f"WHEN '{membership_type}' THEN '{role_code}'"
    for membership_type, role_code in _WS_MEMBERSHIP_ROLE.items()
)


def _access_joins(schema: str) -> str:
    return f"""
    JOIN {schema}."17_fct_user_groups" g ON g.id = gm.group_id
    JOIN {schema}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
    JOIN {schema}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
    JOIN {schema}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
    JOIN {schema}."14_dim_feature_flags" ff ON ff.code = fp.feature_flag_code
    JOIN {schema}."11_dim_feature_flag_categories" cat ON cat.code = ff.feature_flag_category_code
    JOIN {schema}."12_dim_feature_permission_actions" pa ON pa.code = fp.permission_action_code
    """


@instrument_class_methods(namespace="access_context.repository", logger_name="backend.access_context.repository.instrumentation")
class AccessContextRepository:
    async def get_user_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        property_key: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f"""
            SELECT property_value
            FROM {SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = $2
            LIMIT 1
            """,
            user_id,
            property_key,
        )
        return str(row["property_value"]) if row else None

    async def get_first_org_id_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f"""
            SELECT m.org_id::text AS org_id
            FROM {SCHEMA}."31_lnk_org_memberships" m
            JOIN {SCHEMA}."29_fct_orgs" o ON o.id = m.org_id
            WHERE m.user_id = $1
              AND m.is_active = TRUE
              AND m.is_deleted = FALSE
              AND o.is_deleted = FALSE
            ORDER BY
                CASE m.membership_type
                    WHEN 'owner' THEN 1
                    WHEN 'admin' THEN 2
                    WHEN 'member' THEN 3
                    WHEN 'viewer' THEN 4
                    ELSE 5
                END,
                o.created_at,
                o.name
            LIMIT 1
            """,
            user_id,
        )
        return str(row["org_id"]) if row else None

    async def get_first_workspace_id_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        org_id: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f"""
            SELECT m.workspace_id::text AS workspace_id
            FROM {SCHEMA}."36_lnk_workspace_memberships" m
            JOIN {SCHEMA}."34_fct_workspaces" w ON w.id = m.workspace_id
            WHERE m.user_id = $1
              AND w.org_id = $2
              AND m.is_active = TRUE
              AND m.is_deleted = FALSE
              AND w.is_deleted = FALSE
            ORDER BY
                CASE m.membership_type
                    WHEN 'owner' THEN 1
                    WHEN 'admin' THEN 2
                    WHEN 'contributor' THEN 3
                    WHEN 'viewer' THEN 4
                    ELSE 5
                END,
                CASE w.workspace_type_code
                    WHEN 'project' THEN 1
                    WHEN 'sandbox' THEN 2
                    ELSE 3
                END,
                w.created_at,
                w.name
            LIMIT 1
            """,
            user_id,
            org_id,
        )
        return str(row["workspace_id"]) if row else None

    async def get_platform_actions(
        self, connection: asyncpg.Connection, *, user_id: str
    ) -> list[UserAccessAction]:
        """All actions the user holds through platform-scoped groups (scope_org_id IS NULL).
        This includes platform-scope flags (super admin capabilities) AND org/workspace-scope
        flags assigned at the platform level (e.g. super admins who can manage any org)."""
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT {_ACCESS_COLS}
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            {_access_joins(SCHEMA)}
            WHERE gm.user_id = $1
              AND {_ACTIVE_FILTERS}
              AND g.scope_org_id IS NULL AND g.scope_workspace_id IS NULL
            ORDER BY cat.code, ff.code, pa.code
            """,
            user_id,
        )
        return [_row_to_action(r) for r in rows]

    async def get_org_actions(
        self, connection: asyncpg.Connection, *, user_id: str, org_id: str
    ) -> list[UserAccessAction]:
        """Actions effective within the selected org.

        This includes platform-scoped capabilities granted through org-scoped
        groups, which is how org admins inherit GRC and sandbox access.
        Product-scoped actions are returned separately through
        ``get_product_actions``.
        """
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT *
            FROM (
                SELECT {_ACCESS_COLS}
                FROM {SCHEMA}."18_lnk_group_memberships" gm
                {_access_joins(SCHEMA)}
                WHERE gm.user_id = $1
                  AND {_ACTIVE_FILTERS}
                  AND (
                      (g.scope_org_id IS NULL AND g.scope_workspace_id IS NULL)
                      OR g.scope_org_id = $2
                  )
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."31_lnk_org_memberships" om
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = CASE om.membership_type {_ORG_CASE} ELSE NULL END
                  AND r.is_deleted = FALSE
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE om.user_id = $1
                  AND om.org_id = $2
                  AND om.is_active = TRUE
                  AND om.is_deleted = FALSE
                  AND (om.effective_to IS NULL OR om.effective_to > NOW())
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."47_lnk_grc_role_assignments" gra
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = gra.grc_role_code
                  AND r.is_deleted = FALSE
                  AND r.role_level_code = 'workspace'
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE gra.user_id = $1
                  AND gra.org_id = $2
                  AND gra.revoked_at IS NULL
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org')
            ) AS actions
            ORDER BY category_code, feature_code, action_code
            """,
            user_id,
            org_id,
        )
        return [_row_to_action(r) for r in rows]

    async def get_workspace_actions(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        org_id: str,
        workspace_id: str,
    ) -> list[UserAccessAction]:
        """Actions effective within the selected workspace.

        This includes platform-scoped capabilities granted through org/workspace
        groups. Product-scoped actions are returned separately through
        ``get_product_actions``.
        """
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT *
            FROM (
                SELECT {_ACCESS_COLS}
                FROM {SCHEMA}."18_lnk_group_memberships" gm
                {_access_joins(SCHEMA)}
                WHERE gm.user_id = $1
                  AND {_ACTIVE_FILTERS}
                  AND (
                      (g.scope_org_id IS NULL AND g.scope_workspace_id IS NULL)
                      OR g.scope_org_id = $2
                      OR g.scope_workspace_id = $3
                  )
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org', 'workspace')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."31_lnk_org_memberships" om
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = CASE om.membership_type {_ORG_CASE} ELSE NULL END
                  AND r.is_deleted = FALSE
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE om.user_id = $1
                  AND om.org_id = $2
                  AND om.is_active = TRUE
                  AND om.is_deleted = FALSE
                  AND (om.effective_to IS NULL OR om.effective_to > NOW())
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org', 'workspace')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."36_lnk_workspace_memberships" wm
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = CASE wm.membership_type {_WS_CASE} ELSE NULL END
                  AND r.is_deleted = FALSE
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE wm.user_id = $1
                  AND wm.workspace_id = $3
                  AND wm.is_active = TRUE
                  AND wm.is_deleted = FALSE
                  AND (wm.effective_to IS NULL OR wm.effective_to > NOW())
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org', 'workspace')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."36_lnk_workspace_memberships" wm
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = wm.grc_role_code
                  AND r.is_deleted = FALSE
                  AND r.role_level_code = 'workspace'
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE wm.user_id = $1
                  AND wm.workspace_id = $3
                  AND wm.grc_role_code IS NOT NULL
                  AND wm.is_active = TRUE
                  AND wm.is_deleted = FALSE
                  AND (wm.effective_to IS NULL OR wm.effective_to > NOW())
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org', 'workspace')

                UNION

                SELECT
                    ff.code  AS feature_code,
                    ff.name  AS feature_name,
                    pa.code  AS action_code,
                    cat.code AS category_code,
                    ff.access_mode,
                    ff.env_dev,
                    ff.env_staging,
                    ff.env_prod
                FROM {SCHEMA}."47_lnk_grc_role_assignments" gra
                JOIN {SCHEMA}."16_fct_roles" r
                  ON r.code = gra.grc_role_code
                  AND r.is_deleted = FALSE
                  AND r.role_level_code = 'workspace'
                JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp
                  ON rfp.role_id = r.id
                  AND rfp.is_active = TRUE
                  AND rfp.is_deleted = FALSE
                JOIN {SCHEMA}."15_dim_feature_permissions" fp
                  ON fp.id = rfp.feature_permission_id
                JOIN {SCHEMA}."14_dim_feature_flags" ff
                  ON ff.code = fp.feature_flag_code
                JOIN {SCHEMA}."11_dim_feature_flag_categories" cat
                  ON cat.code = ff.feature_flag_category_code
                JOIN {SCHEMA}."12_dim_feature_permission_actions" pa
                  ON pa.code = fp.permission_action_code
                WHERE gra.user_id = $1
                  AND gra.org_id = $2
                  AND gra.revoked_at IS NULL
                  AND COALESCE(ff.feature_scope, 'platform') IN ('platform', 'org', 'workspace')
            ) AS actions
            ORDER BY category_code, feature_code, action_code
            """,
            user_id,
            org_id,
            workspace_id,
        )
        return [_row_to_action(r) for r in rows]

    async def get_org_info(
        self, connection: asyncpg.Connection, org_id: str
    ) -> OrgInfo | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, name, code AS slug, org_type_code
            FROM {SCHEMA}."29_fct_orgs"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            org_id,
        )
        if not row:
            return None
        return OrgInfo(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            org_type_code=row["org_type_code"],
        )

    async def get_product_actions(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        org_id: str,
        workspace_id: str,
        product_id: str,
    ) -> list[UserAccessAction]:
        """Product-scoped groups + product-scope flags tied to this product."""
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT {_ACCESS_COLS}
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            {_access_joins(SCHEMA)}
            WHERE gm.user_id = $1
              AND {_ACTIVE_FILTERS}
              AND (
                  (g.scope_org_id IS NULL AND g.scope_workspace_id IS NULL)
                  OR g.scope_org_id = $2
                  OR g.scope_workspace_id = $3
              )
              AND ff.feature_scope = 'product'
              AND ff.product_id = $4
            ORDER BY cat.code, ff.code, pa.code
            """,
            user_id,
            org_id,
            workspace_id,
            product_id,
        )
        return [_row_to_action(r) for r in rows]

    async def get_workspace_info(
        self, connection: asyncpg.Connection, workspace_id: str
    ) -> WorkspaceInfo | None:
        row = await connection.fetchrow(
            f"""
            SELECT w.id, w.org_id, w.name, w.code AS slug, w.workspace_type_code,
                   w.product_id, p.name AS product_name, p.code AS product_code
            FROM {SCHEMA}."34_fct_workspaces" w
            LEFT JOIN {SCHEMA}."24_fct_products" p ON p.id = w.product_id
            WHERE w.id = $1 AND w.is_deleted = FALSE
            """,
            workspace_id,
        )
        if not row:
            return None
        return WorkspaceInfo(
            id=row["id"],
            org_id=row["org_id"],
            name=row["name"],
            slug=row["slug"],
            workspace_type_code=row["workspace_type_code"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            product_code=row["product_code"],
        )

    async def get_user_access_actions(
        self, connection: asyncpg.Connection, *, user_id: str
    ) -> list[UserAccessAction]:
        """Legacy flat query (no scope filter). Used by older tests."""
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT {_ACCESS_COLS}
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            {_access_joins(SCHEMA)}
            WHERE gm.user_id = $1
              AND {_ACTIVE_FILTERS}
            ORDER BY cat.code, ff.code, pa.code
            """,
            user_id,
        )
        return [_row_to_action(r) for r in rows]


def _row_to_action(r) -> UserAccessAction:
    return UserAccessAction(
        feature_code=r["feature_code"],
        feature_name=r["feature_name"],
        action_code=r["action_code"],
        category_code=r["category_code"],
        access_mode=r["access_mode"],
        env_dev=r["env_dev"],
        env_staging=r["env_staging"],
        env_prod=r["env_prod"],
    )
