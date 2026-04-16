from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import WorkspaceMemberRecord, WorkspaceRecord, WorkspaceTypeRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="workspaces.repository", logger_name="backend.workspaces.repository.instrumentation")
class WorkspaceRepository:
    async def list_workspace_types(
        self, connection: asyncpg.Connection
    ) -> list[WorkspaceTypeRecord]:
        rows = await connection.fetch(
            f"""
            SELECT code, name, description, is_infrastructure_type
            FROM {SCHEMA}."33_dim_workspace_types"
            ORDER BY name
            """
        )
        return [
            WorkspaceTypeRecord(
                code=r["code"],
                name=r["name"],
                description=r["description"],
                is_infrastructure_type=r["is_infrastructure_type"],
            )
            for r in rows
        ]

    async def workspace_type_exists(
        self, connection: asyncpg.Connection, workspace_type_code: str
    ) -> bool:
        value = await connection.fetchval(
            f"""
            SELECT 1
            FROM {SCHEMA}."33_dim_workspace_types"
            WHERE code = $1
            """,
            workspace_type_code,
        )
        return value is not None

    async def list_workspaces(
        self, connection: asyncpg.Connection, *, org_id: str
    ) -> list[WorkspaceRecord]:
        """Return all workspaces in an org (org-admin path)."""
        rows = await connection.fetch(
            f"""
            SELECT id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."34_fct_workspaces"
            WHERE org_id = $1 AND is_deleted = FALSE
            ORDER BY name
            """,
            org_id,
        )
        return [_row_to_ws(r) for r in rows]

    async def list_workspaces_for_user(
        self, connection: asyncpg.Connection, *, user_id: str, org_id: str
    ) -> list[WorkspaceRecord]:
        """Return only workspaces the user is a member of within the org."""
        rows = await connection.fetch(
            f"""
            SELECT w.id, w.org_id, w.workspace_type_code, w.product_id, w.name, w.code AS slug,
                   w.description, w.is_active, w.created_at::text, w.updated_at::text
            FROM {SCHEMA}."34_fct_workspaces" w
            JOIN {SCHEMA}."36_lnk_workspace_memberships" m
              ON m.workspace_id = w.id AND m.user_id = $1
             AND m.is_active = TRUE AND m.is_deleted = FALSE
            WHERE w.org_id = $2 AND w.is_deleted = FALSE
            ORDER BY w.name
            """,
            user_id,
            org_id,
        )
        return [_row_to_ws(r) for r in rows]

    async def get_workspace_by_id(
        self, connection: asyncpg.Connection, workspace_id: str
    ) -> WorkspaceRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."34_fct_workspaces"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            workspace_id,
        )
        return _row_to_ws(row) if row else None

    async def get_workspace_by_name(
        self, connection: asyncpg.Connection, name: str, org_id: str
    ) -> WorkspaceRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."34_fct_workspaces"
            WHERE LOWER(name) = LOWER($1) AND org_id = $2 AND is_deleted = FALSE
            """,
            name,
            org_id,
        )
        return _row_to_ws(row) if row else None

    async def get_workspace_by_slug(
        self, connection: asyncpg.Connection, slug: str, org_id: str
    ) -> WorkspaceRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."34_fct_workspaces"
            WHERE code = $1 AND org_id = $2 AND is_deleted = FALSE
            """,
            slug,
            org_id,
        )
        return _row_to_ws(row) if row else None

    async def create_workspace(
        self,
        connection: asyncpg.Connection,
        *,
        workspace_id: str,
        org_id: str,
        workspace_type_code: str,
        product_id: str | None,
        name: str,
        slug: str,
        description: str | None,
        created_by: str,
        now: datetime,
    ) -> WorkspaceRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."34_fct_workspaces"
                (
                    id, org_id, workspace_type_code, product_id, code, name, description,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $8, $9, $10, $11, NULL, NULL
            )
            RETURNING id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                      is_active, created_at::text, updated_at::text
            """,
            workspace_id,
            org_id,
            workspace_type_code,
            product_id,
            slug,
            name,
            description or "",
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_ws(row)

    async def update_workspace(
        self,
        connection: asyncpg.Connection,
        workspace_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        product_id: str | None = None,
        is_disabled: bool | None = None,
        updated_by: str,
        now: datetime,
    ) -> WorkspaceRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if name is not None:
            fields.append(f"name = ${idx}")
            values.append(name)
            idx += 1
        if description is not None:
            fields.append(f"description = ${idx}")
            values.append(description)
            idx += 1
        if product_id is not None:
            fields.append(f"product_id = ${idx}")
            values.append(product_id)
            idx += 1
        if is_disabled is not None:
            fields.append(f"is_active = ${idx}")
            values.append(not is_disabled)
            idx += 1

        if not fields:
            return await self.get_workspace_by_id(connection, workspace_id)

        values.append(workspace_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."34_fct_workspaces"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, org_id, workspace_type_code, product_id, name, code AS slug, description,
                      is_active, created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_ws(row) if row else None

    async def list_workspace_members(
        self, connection: asyncpg.Connection, workspace_id: str
    ) -> list[WorkspaceMemberRecord]:
        rows = await connection.fetch(
            f"""
            SELECT m.id, m.workspace_id, m.user_id, m.membership_type AS role, m.is_active,
                   m.effective_from::text AS joined_at,
                   m.grc_role_code,
                   v.email, dn.property_value AS display_name
            FROM {SCHEMA}."36_lnk_workspace_memberships" m
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = m.user_id
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
              ON dn.user_id = m.user_id AND dn.property_key = 'display_name'
            WHERE m.workspace_id = $1 AND m.is_active = TRUE AND m.is_deleted = FALSE
            ORDER BY m.effective_from
            """,
            workspace_id,
        )
        return [_row_to_member(r) for r in rows]

    async def add_workspace_member(
        self,
        connection: asyncpg.Connection,
        *,
        membership_id: str,
        workspace_id: str,
        user_id: str,
        role: str,
        created_by: str,
        now: datetime,
    ) -> WorkspaceMemberRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."36_lnk_workspace_memberships" (
                id, workspace_id, user_id, membership_type, membership_status,
                effective_from, effective_to,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                $1, $2, $3, $4, 'active',
                $5, NULL,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $6, $7, $8, $9, NULL, NULL
            )
            ON CONFLICT (workspace_id, user_id) WHERE is_deleted = FALSE
            DO UPDATE SET
                membership_type = EXCLUDED.membership_type,
                membership_status = 'active',
                effective_from = EXCLUDED.effective_from,
                effective_to = NULL,
                is_active = TRUE,
                is_deleted = FALSE,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by,
                deleted_at = NULL,
                deleted_by = NULL
            RETURNING id, workspace_id, user_id, membership_type AS role, is_active, effective_from::text AS joined_at
            """,
            membership_id,
            workspace_id,
            user_id,
            role,
            now,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_member(row)

    async def get_workspace_member(
        self,
        connection: asyncpg.Connection,
        workspace_id: str,
        user_id: str,
    ) -> WorkspaceMemberRecord | None:
        """Fetch a single workspace membership record.

        Args:
            connection: Active asyncpg database connection.
            workspace_id: UUID of the workspace.
            user_id: UUID of the user.

        Returns:
            WorkspaceMemberRecord or None if not found / deleted.
        """
        row = await connection.fetchrow(
            f"""
            SELECT m.id, m.workspace_id, m.user_id, m.membership_type AS role, m.is_active,
                   m.effective_from::text AS joined_at,
                   m.grc_role_code,
                   v.email, dn.property_value AS display_name
            FROM {SCHEMA}."36_lnk_workspace_memberships" m
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = m.user_id
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
              ON dn.user_id = m.user_id AND dn.property_key = 'display_name'
            WHERE m.workspace_id = $1 AND m.user_id = $2
              AND m.is_active = TRUE AND m.is_deleted = FALSE
            """,
            workspace_id,
            user_id,
        )
        return _row_to_member(row) if row else None

    async def remove_workspace_member(
        self,
        connection: asyncpg.Connection,
        *,
        workspace_id: str,
        user_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."36_lnk_workspace_memberships"
            SET
                is_active = FALSE,
                is_deleted = TRUE,
                membership_status = 'removed',
                effective_to = $1,
                updated_at = $2,
                updated_by = $3,
                deleted_at = $4,
                deleted_by = $5
            WHERE workspace_id = $6 AND user_id = $7 AND is_deleted = FALSE
            """,
            now,
            now,
            deleted_by,
            now,
            deleted_by,
            workspace_id,
            user_id,
        )
        return result != "UPDATE 0"


def _row_to_ws(r) -> WorkspaceRecord:
    return WorkspaceRecord(
        id=r["id"],
        org_id=r["org_id"],
        workspace_type_code=r["workspace_type_code"],
        product_id=r["product_id"],
        name=r["name"],
        slug=r["slug"],
        description=r["description"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_member(r) -> WorkspaceMemberRecord:
    return WorkspaceMemberRecord(
        id=r["id"],
        workspace_id=r["workspace_id"],
        user_id=r["user_id"],
        role=r["role"],
        is_active=r["is_active"],
        joined_at=r["joined_at"],
        email=r.get("email"),
        display_name=r.get("display_name"),
        grc_role_code=r.get("grc_role_code"),
    )
