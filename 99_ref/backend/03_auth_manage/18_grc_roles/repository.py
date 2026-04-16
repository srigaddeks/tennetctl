"""Raw SQL repository for GRC role assignments and access grants."""
from __future__ import annotations

from importlib import import_module

import asyncpg

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"03_auth_manage"'

_ROLE_CATEGORIES: dict[str, str] = {
    "grc_practitioner": "internal",
    "grc_engineer": "internal",
    "grc_ciso": "internal",
    "grc_lead_auditor": "auditor",
    "grc_staff_auditor": "auditor",
    "grc_vendor": "vendor",
}


@instrument_class_methods(namespace="grc_roles.repository", logger_name="backend.grc_roles.repository")
class GrcRoleRepository:
    """Data access layer for GRC role assignments and access grants."""

    async def list_assignments(
        self,
        conn: asyncpg.Connection,
        *,
        org_id: str,
        grc_role_code: str | None = None,
        user_id: str | None = None,
    ) -> list[dict]:
        """List active GRC role assignments for an org with optional filters.

        Args:
            conn: Active asyncpg database connection.
            org_id: UUID of the org to query.
            grc_role_code: Optional filter by role code.
            user_id: Optional filter by user.

        Returns:
            List of assignment dicts from v_grc_team view.
        """
        conditions = ["org_id = $1"]
        params: list = [org_id]
        idx = 2

        if grc_role_code:
            conditions.append(f"grc_role_code = ${idx}")
            params.append(grc_role_code)
            idx += 1

        if user_id:
            conditions.append(f"user_id = ${idx}")
            params.append(user_id)
            idx += 1

        where = " AND ".join(conditions)
        rows = await conn.fetch(
            f"""
            SELECT assignment_id, org_id, user_id, grc_role_code,
                   role_name, role_description, email, display_name,
                   assigned_by, assigned_at, active_grant_count, created_at
            FROM {SCHEMA}."v_grc_team"
            WHERE {where}
            ORDER BY grc_role_code, display_name, email
            """,
            *params,
        )
        return [dict(r) for r in rows]

    async def get_assignment_by_id(
        self, conn: asyncpg.Connection, assignment_id: str
    ) -> dict | None:
        """Fetch a single assignment by ID.

        Args:
            conn: Active asyncpg database connection.
            assignment_id: UUID of the assignment.

        Returns:
            Assignment dict or None if not found.
        """
        row = await conn.fetchrow(
            f"""
            SELECT assignment_id, org_id, user_id, grc_role_code,
                   role_name, role_description, email, display_name,
                   assigned_by, assigned_at, active_grant_count, created_at
            FROM {SCHEMA}."v_grc_team"
            WHERE assignment_id = $1
            """,
            assignment_id,
        )
        return dict(row) if row else None

    async def create_assignment(
        self,
        conn: asyncpg.Connection,
        *,
        assignment_id: str,
        org_id: str,
        user_id: str,
        grc_role_code: str,
        assigned_by: str | None,
        assigned_at,
    ) -> None:
        """Insert a new GRC role assignment.

        Args:
            conn: Active asyncpg database connection.
            assignment_id: UUID for the new assignment.
            org_id: Org the role belongs to.
            user_id: User receiving the role.
            grc_role_code: GRC role code.
            assigned_by: Actor who assigned the role.
            assigned_at: Timestamp of assignment.
        """
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}."47_lnk_grc_role_assignments"
                (id, org_id, user_id, grc_role_code, assigned_by, assigned_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            assignment_id, org_id, user_id, grc_role_code, assigned_by, assigned_at, assigned_at,
        )

    async def find_active_assignment(
        self,
        conn: asyncpg.Connection,
        *,
        org_id: str,
        user_id: str,
        grc_role_code: str,
    ) -> dict | None:
        """Find an existing active assignment for the given user+org+role.

        Args:
            conn: Active asyncpg database connection.
            org_id: Org to check.
            user_id: User to check.
            grc_role_code: Role code to check.

        Returns:
            Assignment row dict or None.
        """
        row = await conn.fetchrow(
            f"""
            SELECT id, org_id, user_id, grc_role_code, assigned_by, assigned_at, created_at
            FROM {SCHEMA}."47_lnk_grc_role_assignments"
            WHERE org_id = $1 AND user_id = $2 AND grc_role_code = $3
              AND revoked_at IS NULL
            """,
            org_id, user_id, grc_role_code,
        )
        return dict(row) if row else None

    async def revoke_assignment(
        self,
        conn: asyncpg.Connection,
        *,
        assignment_id: str,
        revoked_by: str,
        revoked_at,
    ) -> bool:
        """Revoke a GRC role assignment. Also revokes all linked access grants.

        Args:
            conn: Active asyncpg database connection.
            assignment_id: UUID of the assignment to revoke.
            revoked_by: Actor who revoked.
            revoked_at: Timestamp of revocation.

        Returns:
            True if a row was updated, False if not found or already revoked.
        """
        # Revoke all linked access grants first
        await conn.execute(
            f"""
            UPDATE {SCHEMA}."48_lnk_grc_access_grants"
            SET revoked_at = $1, revoked_by = $2
            WHERE grc_role_assignment_id = $3 AND revoked_at IS NULL
            """,
            revoked_at, revoked_by, assignment_id,
        )
        result = await conn.execute(
            f"""
            UPDATE {SCHEMA}."47_lnk_grc_role_assignments"
            SET revoked_at = $1, revoked_by = $2
            WHERE id = $3 AND revoked_at IS NULL
            """,
            revoked_at, revoked_by, assignment_id,
        )
        return result.split()[-1] != "0"

    # ── Access grants ──────────────────────────────────────────────────────────

    async def list_grants(
        self,
        conn: asyncpg.Connection,
        *,
        assignment_id: str,
    ) -> list[dict]:
        """List active access grants for a role assignment.

        Args:
            conn: Active asyncpg database connection.
            assignment_id: UUID of the role assignment.

        Returns:
            List of grant dicts.
        """
        rows = await conn.fetch(
            f"""
            SELECT g.id, g.grc_role_assignment_id, g.scope_type, g.scope_id,
                   g.granted_by, g.granted_at, g.created_at,
                   CASE g.scope_type
                       WHEN 'workspace' THEN (
                           SELECT w.name FROM {SCHEMA}."34_fct_workspaces" w WHERE w.id = g.scope_id::UUID
                       )
                       WHEN 'framework' THEN (
                           SELECT fp.property_value
                           FROM "05_grc_library"."16_fct_framework_deployments" fd
                           JOIN "05_grc_library"."20_dtl_framework_properties" fp
                             ON fp.framework_id = fd.framework_id AND fp.property_key = 'name'
                           WHERE fd.id = g.scope_id::UUID
                           LIMIT 1
                       )
                       WHEN 'engagement' THEN (
                           SELECT e.engagement_code
                           FROM "12_engagements"."10_fct_audit_engagements" e
                           WHERE e.id = g.scope_id::UUID
                           LIMIT 1
                       )
                       ELSE NULL
                   END AS scope_name
            FROM {SCHEMA}."48_lnk_grc_access_grants" g
            WHERE g.grc_role_assignment_id = $1 AND g.revoked_at IS NULL
            ORDER BY g.scope_type, g.granted_at
            """,
            assignment_id,
        )
        return [dict(r) for r in rows]

    async def create_grant(
        self,
        conn: asyncpg.Connection,
        *,
        grant_id: str,
        grc_role_assignment_id: str,
        scope_type: str,
        scope_id: str,
        granted_by: str | None,
        granted_at,
    ) -> None:
        """Insert a new access grant for a role assignment.

        Args:
            conn: Active asyncpg database connection.
            grant_id: UUID for the new grant.
            grc_role_assignment_id: FK to the role assignment.
            scope_type: 'workspace', 'framework', or 'engagement'.
            scope_id: UUID of the scoped entity.
            granted_by: Actor who granted access.
            granted_at: Timestamp of grant.
        """
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}."48_lnk_grc_access_grants"
                (id, grc_role_assignment_id, scope_type, scope_id, granted_by, granted_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            grant_id, grc_role_assignment_id, scope_type, scope_id,
            granted_by, granted_at, granted_at,
        )

    async def find_active_grant(
        self,
        conn: asyncpg.Connection,
        *,
        grc_role_assignment_id: str,
        scope_type: str,
        scope_id: str,
    ) -> dict | None:
        """Find an existing active grant.

        Args:
            conn: Active asyncpg database connection.
            grc_role_assignment_id: FK to role assignment.
            scope_type: Scope type to check.
            scope_id: Scope entity ID to check.

        Returns:
            Grant row dict or None.
        """
        row = await conn.fetchrow(
            f"""
            SELECT id, grc_role_assignment_id, scope_type, scope_id,
                   granted_by, granted_at, created_at
            FROM {SCHEMA}."48_lnk_grc_access_grants"
            WHERE grc_role_assignment_id = $1
              AND scope_type = $2
              AND scope_id = $3
              AND revoked_at IS NULL
            """,
            grc_role_assignment_id, scope_type, scope_id,
        )
        return dict(row) if row else None

    async def revoke_grant(
        self,
        conn: asyncpg.Connection,
        *,
        grant_id: str,
        revoked_by: str,
        revoked_at,
    ) -> bool:
        """Revoke an access grant.

        Args:
            conn: Active asyncpg database connection.
            grant_id: UUID of the grant to revoke.
            revoked_by: Actor who revoked.
            revoked_at: Timestamp of revocation.

        Returns:
            True if a row was updated.
        """
        result = await conn.execute(
            f"""
            UPDATE {SCHEMA}."48_lnk_grc_access_grants"
            SET revoked_at = $1, revoked_by = $2
            WHERE id = $3 AND revoked_at IS NULL
            """,
            revoked_at, revoked_by, grant_id,
        )
        return result.split()[-1] != "0"

    # ── Team view ──────────────────────────────────────────────────────────────

    async def get_team(
        self,
        conn: asyncpg.Connection,
        *,
        org_id: str,
        workspace_id: str | None = None,
        engagement_id: str | None = None,
    ) -> list[dict]:
        """Get full GRC team for an org with optional scope filter.

        When workspace_id or engagement_id is provided, returns only members
        who have an access grant for that scope (plus org-wide members with
        no grants = they have org-wide access by default).

        Args:
            conn: Active asyncpg database connection.
            org_id: Org to query.
            workspace_id: Optional workspace scope filter.
            engagement_id: Optional engagement scope filter.

        Returns:
            List of team member dicts with nested grant info.
        """
        if workspace_id or engagement_id:
            # Filtered: show members with matching grants OR no grants (org-wide)
            scope_conditions = []
            params: list = [org_id]
            idx = 2

            if workspace_id:
                scope_conditions.append(
                    f"(g.scope_type = 'workspace' AND g.scope_id = ${idx})"
                )
                params.append(workspace_id)
                idx += 1

            if engagement_id:
                scope_conditions.append(
                    f"(g.scope_type = 'engagement' AND g.scope_id = ${idx})"
                )
                params.append(engagement_id)
                idx += 1

            scope_filter = " OR ".join(scope_conditions)
            rows = await conn.fetch(
                f"""
                SELECT DISTINCT ON (ra.id)
                    ra.id AS assignment_id, ra.org_id, ra.user_id, ra.grc_role_code,
                    r.name AS role_name,
                    email.property_value AS email,
                    dn.property_value AS display_name,
                    ra.assigned_at
                FROM {SCHEMA}."47_lnk_grc_role_assignments" ra
                JOIN {SCHEMA}."16_fct_roles" r
                    ON r.code = ra.grc_role_code AND r.is_deleted = FALSE AND r.role_level_code = 'workspace'
                LEFT JOIN {SCHEMA}."05_dtl_user_properties" email
                    ON email.user_id = ra.user_id AND email.property_key = 'email'
                LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
                    ON dn.user_id = ra.user_id AND dn.property_key = 'display_name'
                LEFT JOIN {SCHEMA}."48_lnk_grc_access_grants" g
                    ON g.grc_role_assignment_id = ra.id AND g.revoked_at IS NULL
                WHERE ra.org_id = $1
                  AND ra.revoked_at IS NULL
                  AND (
                      -- Members with no grants = org-wide access
                      NOT EXISTS (
                          SELECT 1 FROM {SCHEMA}."48_lnk_grc_access_grants" g2
                          WHERE g2.grc_role_assignment_id = ra.id AND g2.revoked_at IS NULL
                      )
                      -- OR members with matching scope grant
                      OR ({scope_filter})
                  )
                ORDER BY ra.id, ra.grc_role_code, display_name, email
                """,
                *params,
            )
        else:
            # Unfiltered: show all org members
            rows = await conn.fetch(
                f"""
                SELECT assignment_id, org_id, user_id, grc_role_code,
                       role_name, email, display_name, assigned_at
                FROM {SCHEMA}."v_grc_team"
                WHERE org_id = $1
                ORDER BY grc_role_code, display_name, email
                """,
                org_id,
            )
        return [dict(r) for r in rows]

    async def sync_workspace_membership_grc_role(
        self,
        conn: asyncpg.Connection,
        *,
        user_id: str,
        workspace_id: str,
        grc_role_code: str | None,
    ) -> None:
        """Sync grc_role_code on workspace membership for backward compatibility.

        Args:
            conn: Active asyncpg database connection.
            user_id: User whose membership to update.
            workspace_id: Workspace to update.
            grc_role_code: Role code to set, or None to clear.
        """
        await conn.execute(
            f"""
            UPDATE {SCHEMA}."36_lnk_workspace_memberships"
            SET grc_role_code = $1, updated_at = NOW()
            WHERE user_id = $2::UUID AND workspace_id = $3::UUID
              AND is_active = TRUE AND is_deleted = FALSE
            """,
            grc_role_code, user_id, workspace_id,
        )
