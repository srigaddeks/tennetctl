from __future__ import annotations

from asyncpg import Pool


class PortalViewRepository:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    # ── Read ─────────────────────────────────────────────────────────────────

    async def list_views(self, include_inactive: bool = False) -> list[dict]:
        where = "" if include_inactive else "WHERE is_active = TRUE"
        sql = f"""
            SELECT id, code, name, description, color, icon, sort_order, is_active, default_route
            FROM "03_auth_manage"."50_dim_portal_views"
            {where}
            ORDER BY sort_order
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(r) for r in rows]

    async def get_view(self, code: str) -> dict | None:
        sql = """
            SELECT id, code, name, description, color, icon, sort_order, is_active, default_route
            FROM "03_auth_manage"."50_dim_portal_views"
            WHERE code = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, code)
        return dict(row) if row else None

    async def create_view(
        self, *, code: str, name: str, description: str | None,
        color: str | None, icon: str | None, sort_order: int,
        default_route: str | None,
    ) -> dict:
        sql = """
            INSERT INTO "03_auth_manage"."50_dim_portal_views"
                (code, name, description, color, icon, sort_order, is_active, default_route)
            VALUES ($1, $2, $3, $4, $5, $6, TRUE, $7)
            RETURNING id, code, name, description, color, icon, sort_order, is_active, default_route
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, code, name, description, color, icon, sort_order, default_route)
        return dict(row)  # type: ignore[arg-type]

    async def update_view(
        self, code: str, *,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
        default_route: str | None = None,
    ) -> dict | None:
        sets = []
        params: list[object] = []
        idx = 1

        def _add(col: str, val: object) -> None:
            nonlocal idx
            sets.append(f"{col} = ${idx}")
            params.append(val)
            idx += 1

        if name is not None: _add("name", name)
        if description is not None: _add("description", description)
        if color is not None: _add("color", color)
        if icon is not None: _add("icon", icon)
        if sort_order is not None: _add("sort_order", sort_order)
        if is_active is not None: _add("is_active", is_active)
        if default_route is not None: _add("default_route", default_route)

        if not sets:
            return await self.get_view(code)

        params.append(code)
        sql = f"""
            UPDATE "03_auth_manage"."50_dim_portal_views"
            SET {", ".join(sets)}
            WHERE code = ${idx}
            RETURNING id, code, name, description, color, icon, sort_order, is_active, default_route
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
        return dict(row) if row else None

    async def delete_view(self, code: str) -> dict | None:
        sql = """
            DELETE FROM "03_auth_manage"."50_dim_portal_views" 
            WHERE code = $1
            RETURNING id, code
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, code)
        return dict(row) if row else None

    async def add_route(
        self, *, view_code: str, route_prefix: str, is_read_only: bool,
        sort_order: int, sidebar_label: str | None, sidebar_icon: str | None,
        sidebar_section: str | None,
    ) -> dict:
        sql = """
            INSERT INTO "03_auth_manage"."52_dtl_view_routes"
                (view_code, route_prefix, is_read_only, sort_order,
                 sidebar_label, sidebar_icon, sidebar_section)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (view_code, route_prefix) DO UPDATE SET
                is_read_only = EXCLUDED.is_read_only,
                sort_order = EXCLUDED.sort_order,
                sidebar_label = EXCLUDED.sidebar_label,
                sidebar_icon = EXCLUDED.sidebar_icon,
                sidebar_section = EXCLUDED.sidebar_section
            RETURNING view_code, route_prefix, is_read_only, sort_order,
                      sidebar_label, sidebar_icon, sidebar_section
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql, view_code, route_prefix, is_read_only, sort_order,
                sidebar_label, sidebar_icon, sidebar_section,
            )
        return dict(row)  # type: ignore[arg-type]

    async def remove_route(self, view_code: str, route_prefix: str) -> bool:
        sql = """
            DELETE FROM "03_auth_manage"."52_dtl_view_routes"
            WHERE view_code = $1 AND route_prefix = $2
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, view_code, route_prefix)
        return result != "DELETE 0"

    async def list_view_routes(self, view_code: str | None = None) -> list[dict]:
        if view_code:
            sql = """
                SELECT view_code, route_prefix, is_read_only, sort_order,
                       sidebar_label, sidebar_icon, sidebar_section
                FROM "03_auth_manage"."52_dtl_view_routes"
                WHERE view_code = $1
                ORDER BY sort_order
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql, view_code)
        else:
            sql = """
                SELECT view_code, route_prefix, is_read_only, sort_order,
                       sidebar_label, sidebar_icon, sidebar_section
                FROM "03_auth_manage"."52_dtl_view_routes"
                ORDER BY view_code, sort_order
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql)
        return [dict(r) for r in rows]

    async def list_role_views(self, role_id: str) -> list[dict]:
        sql = """
            SELECT rv.role_id::TEXT, rv.view_code
            FROM "03_auth_manage"."51_lnk_role_views" rv
            WHERE rv.role_id = $1::UUID
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, role_id)
        return [dict(r) for r in rows]

    async def list_all_role_view_assignments(self) -> list[dict]:
        sql = """
            SELECT rv.role_id::TEXT, rv.view_code
            FROM "03_auth_manage"."51_lnk_role_views" rv
            ORDER BY rv.role_id, rv.view_code
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(r) for r in rows]

    # ── User view resolution ─────────────────────────────────────────────────
    # Resolves views from ALL role paths (matching _permission_check.py):
    #   1. Platform groups  → group → role → role_views
    #   2. Direct org membership  → CASE → role → role_views
    #   3. Direct workspace membership  → CASE → role → role_views
    #   4. GRC role on workspace membership  → role → role_views

    async def resolve_user_views(self, user_id: str, org_id: str | None = None) -> list[str]:
        """Return distinct view codes the user has access to via all role paths.

        When org_id is provided, org/workspace membership paths are scoped to that
        specific org only. Platform group memberships (Path 1) remain unscoped as
        they grant platform-level access regardless of org context.

        Args:
            user_id: UUID of the user.
            org_id: Optional UUID of the org to scope membership checks to.

        Returns:
            Sorted list of distinct view codes.
        """
        org_filter_om = "AND om.org_id = $2::UUID" if org_id else ""
        org_filter_wm = (
            "AND wm.org_id = $2::UUID" if org_id else ""
        )
        params: list[object] = [user_id] if not org_id else [user_id, org_id]

        sql = f"""
            -- Path 1: Platform groups → role → views (always unscoped — platform level)
            SELECT DISTINCT rv.view_code
            FROM "03_auth_manage"."18_lnk_group_memberships" gm
            JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra
                ON gra.group_id = gm.group_id
                AND gra.is_active = TRUE AND gra.is_deleted = FALSE
                AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
            JOIN "03_auth_manage"."51_lnk_role_views" rv
                ON rv.role_id = gra.role_id
            JOIN "03_auth_manage"."50_dim_portal_views" v
                ON v.code = rv.view_code AND v.is_active = TRUE
            WHERE gm.user_id = $1::UUID
              AND gm.is_active = TRUE AND gm.is_deleted = FALSE
              AND (gm.effective_to IS NULL OR gm.effective_to > NOW())

            UNION

            -- Path 2: Direct org membership → CASE → role → views (scoped to org)
            SELECT DISTINCT rv.view_code
            FROM "03_auth_manage"."31_lnk_org_memberships" om
            JOIN "03_auth_manage"."16_fct_roles" r
                ON r.code = CASE om.membership_type
                    WHEN 'owner' THEN 'org_admin'
                    WHEN 'admin' THEN 'org_admin'
                    WHEN 'member' THEN 'org_member'
                    WHEN 'viewer' THEN 'org_viewer'
                    WHEN 'billing' THEN 'org_viewer'
                    ELSE NULL END
                AND r.is_deleted = FALSE
            JOIN "03_auth_manage"."51_lnk_role_views" rv
                ON rv.role_id = r.id
            JOIN "03_auth_manage"."50_dim_portal_views" v
                ON v.code = rv.view_code AND v.is_active = TRUE
            WHERE om.user_id = $1::UUID
              {org_filter_om}
              AND om.is_active = TRUE AND om.is_deleted = FALSE
              AND (om.effective_to IS NULL OR om.effective_to > NOW())

            UNION

            -- Path 3: Direct workspace membership → CASE → role → views (scoped to org)
            SELECT DISTINCT rv.view_code
            FROM "03_auth_manage"."36_lnk_workspace_memberships" wm
            JOIN "03_auth_manage"."34_fct_workspaces" ws ON ws.id = wm.workspace_id
            JOIN "03_auth_manage"."16_fct_roles" r
                ON r.code = CASE wm.membership_type
                    WHEN 'owner' THEN 'workspace_admin'
                    WHEN 'admin' THEN 'workspace_admin'
                    WHEN 'contributor' THEN 'workspace_contributor'
                    WHEN 'viewer' THEN 'workspace_viewer'
                    WHEN 'readonly' THEN 'workspace_viewer'
                    ELSE NULL END
                AND r.is_deleted = FALSE
            JOIN "03_auth_manage"."51_lnk_role_views" rv
                ON rv.role_id = r.id
            JOIN "03_auth_manage"."50_dim_portal_views" v
                ON v.code = rv.view_code AND v.is_active = TRUE
            WHERE wm.user_id = $1::UUID
              {org_filter_wm.replace('wm.org_id', 'ws.org_id')}
              AND wm.is_active = TRUE AND wm.is_deleted = FALSE
              AND (wm.effective_to IS NULL OR wm.effective_to > NOW())

            UNION

            -- Path 4: GRC role on workspace membership → role → views (scoped to org)
            SELECT DISTINCT rv.view_code
            FROM "03_auth_manage"."36_lnk_workspace_memberships" wm
            JOIN "03_auth_manage"."34_fct_workspaces" ws ON ws.id = wm.workspace_id
            JOIN "03_auth_manage"."16_fct_roles" r
                ON r.code = wm.grc_role_code
                AND r.is_deleted = FALSE
                AND r.role_level_code = 'workspace'
            JOIN "03_auth_manage"."51_lnk_role_views" rv
                ON rv.role_id = r.id
            JOIN "03_auth_manage"."50_dim_portal_views" v
                ON v.code = rv.view_code AND v.is_active = TRUE
            WHERE wm.user_id = $1::UUID
              {org_filter_wm.replace('wm.org_id', 'ws.org_id')}
              AND wm.grc_role_code IS NOT NULL
              AND wm.is_active = TRUE AND wm.is_deleted = FALSE
              AND (wm.effective_to IS NULL OR wm.effective_to > NOW())

            ORDER BY view_code
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        return [r["view_code"] for r in rows]

    async def resolve_grc_role_views(self, user_id: str, org_id: str) -> list[str]:
        """Return view codes from the user's GRC role on workspace membership only.

        Used for users with GRC access grants to restrict portal views to their
        GRC role rather than the broader org membership views.

        Args:
            user_id: UUID of the user.
            org_id: UUID of the org.

        Returns:
            Sorted list of distinct view codes from GRC role path.
        """
        sql = """
            SELECT DISTINCT rv.view_code
            FROM "03_auth_manage"."36_lnk_workspace_memberships" wm
            JOIN "03_auth_manage"."34_fct_workspaces" ws ON ws.id = wm.workspace_id
            JOIN "03_auth_manage"."16_fct_roles" r
                ON r.code = wm.grc_role_code
                AND r.is_deleted = FALSE
                AND r.role_level_code = 'workspace'
            JOIN "03_auth_manage"."51_lnk_role_views" rv
                ON rv.role_id = r.id
            JOIN "03_auth_manage"."50_dim_portal_views" v
                ON v.code = rv.view_code AND v.is_active = TRUE
            WHERE wm.user_id = $1::UUID
              AND ws.org_id = $2::UUID
              AND wm.grc_role_code IS NOT NULL
              AND wm.is_active = TRUE AND wm.is_deleted = FALSE
              AND (wm.effective_to IS NULL OR wm.effective_to > NOW())
            ORDER BY view_code
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, user_id, org_id)
        return [r["view_code"] for r in rows]

    # ── Write ────────────────────────────────────────────────────────────────

    async def assign_view_to_role(self, role_id: str, view_code: str, actor_id: str) -> None:
        sql = """
            INSERT INTO "03_auth_manage"."51_lnk_role_views" (role_id, view_code, created_by)
            VALUES ($1::UUID, $2, $3::UUID)
            ON CONFLICT (role_id, view_code) DO NOTHING
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, role_id, view_code, actor_id)

    async def revoke_view_from_role(self, role_id: str, view_code: str) -> None:
        sql = """
            DELETE FROM "03_auth_manage"."51_lnk_role_views"
            WHERE role_id = $1::UUID AND view_code = $2
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, role_id, view_code)
