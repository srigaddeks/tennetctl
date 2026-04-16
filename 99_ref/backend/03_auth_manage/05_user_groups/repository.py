from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import uuid4

import asyncpg

from .models import GroupMemberRecord, GroupRecord, GroupRoleRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_SELECT_GROUP_COLS = """
    id, code, name, description, role_level_code, tenant_key,
    parent_group_id, scope_org_id, scope_workspace_id,
    is_active, is_system, is_locked, created_at, updated_at
"""


@instrument_class_methods(namespace="user_groups.repository", logger_name="backend.user_groups.repository.instrumentation")
class UserGroupRepository:
    async def list_groups(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope_org_id: str | None = None,
    ) -> list[GroupRecord]:
        if scope_org_id is not None:
            rows = await connection.fetch(
                f"""
                SELECT {_SELECT_GROUP_COLS}
                FROM {SCHEMA}."17_fct_user_groups"
                WHERE tenant_key = $1
                  AND scope_org_id = $2
                  AND is_deleted = FALSE
                ORDER BY role_level_code, parent_group_id NULLS FIRST, code
                """,
                tenant_key,
                scope_org_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT {_SELECT_GROUP_COLS}
                FROM {SCHEMA}."17_fct_user_groups"
                WHERE tenant_key = $1 AND is_deleted = FALSE
                ORDER BY role_level_code, parent_group_id NULLS FIRST, code
                """,
                tenant_key,
            )
        return [_row_to_group(r) for r in rows]

    async def get_group_by_id(
        self, connection: asyncpg.Connection, group_id: str
    ) -> GroupRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_SELECT_GROUP_COLS}
            FROM {SCHEMA}."17_fct_user_groups"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            group_id,
        )
        return _row_to_group(row) if row else None

    async def create_group(
        self,
        connection: asyncpg.Connection,
        *,
        code: str,
        name: str,
        description: str,
        role_level_code: str,
        tenant_key: str,
        parent_group_id: str | None,
        scope_org_id: str | None,
        created_by: str,
        now: datetime,
    ) -> GroupRecord:
        group_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."17_fct_user_groups" (
                id, tenant_key, role_level_code, code, name, description,
                parent_group_id, scope_org_id, scope_workspace_id,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NULL,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $9, $10, $11, $12, NULL, NULL)
            """,
            group_id, tenant_key, role_level_code, code, name, description,
            parent_group_id, scope_org_id,
            now, now, created_by, created_by,
        )
        row = await connection.fetchrow(
            f"SELECT {_SELECT_GROUP_COLS} FROM {SCHEMA}.\"17_fct_user_groups\" WHERE id = $1",
            group_id,
        )
        return _row_to_group(row)  # type: ignore[arg-type]

    async def update_group(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        name: str | None,
        description: str | None,
        parent_group_id: str | None = ...,  # type: ignore[assignment]
        is_disabled: bool | None = None,
        updated_by: str,
        now: datetime,
    ) -> GroupRecord | None:
        sets: list[str] = ["updated_at = $1", "updated_by = $2"]
        params: list[object] = [now, updated_by]
        idx = 3

        def _add(col: str, val: object) -> None:
            nonlocal idx
            sets.append(f"{col} = ${idx}")
            params.append(val)
            idx += 1

        if name is not None:
            _add("name", name)
        if description is not None:
            _add("description", description)
        # parent_group_id=None means "clear parent"; sentinel ... means "don't touch"
        if parent_group_id is not ...:  # type: ignore[comparison-overlap]
            _add("parent_group_id", parent_group_id)
        if is_disabled is not None:
            _add("is_active", not is_disabled)
            _add("is_disabled", is_disabled)

        params.append(group_id)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."17_fct_user_groups"
            SET {", ".join(sets)}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING {_SELECT_GROUP_COLS}
            """,
            *params,
        )
        return _row_to_group(row) if row else None

    async def delete_group(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."17_fct_user_groups"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE AND is_system = FALSE
            """,
            now, deleted_by, now, deleted_by, group_id,
        )
        return result != "UPDATE 0"

    async def list_group_members(
        self, connection: asyncpg.Connection, group_id: str
    ) -> list[GroupMemberRecord]:
        """List all members of a group with scope (org/workspace) resolution.

        Args:
            connection: Active asyncpg database connection.
            group_id: UUID of the group.

        Returns:
            List of group member records with resolved org/workspace names.
        """
        rows = await connection.fetch(
            f"""
            SELECT m.id, m.group_id, m.user_id, m.membership_status,
                   m.effective_from, m.effective_to,
                   v.email,
                   dn.property_value AS display_name,
                   m.scope_org_id::text AS scope_org_id,
                   o.name AS scope_org_name,
                   m.scope_workspace_id::text AS scope_workspace_id,
                   w.name AS scope_workspace_name
            FROM {SCHEMA}."18_lnk_group_memberships" m
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = m.user_id
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
                   ON dn.user_id = m.user_id AND dn.property_key = 'display_name'
            LEFT JOIN {SCHEMA}."29_fct_orgs" o ON o.id = m.scope_org_id
            LEFT JOIN {SCHEMA}."34_fct_workspaces" w ON w.id = m.scope_workspace_id
            WHERE m.group_id = $1 AND m.is_deleted = FALSE AND m.is_active = TRUE
            ORDER BY o.name NULLS FIRST, w.name NULLS FIRST, m.effective_from
            """,
            group_id,
        )
        return [
            GroupMemberRecord(
                id=r["id"], group_id=r["group_id"], user_id=r["user_id"],
                membership_status=r["membership_status"],
                effective_from=r["effective_from"], effective_to=r["effective_to"],
                email=r.get("email"), display_name=r.get("display_name"),
                scope_org_id=r.get("scope_org_id"), scope_org_name=r.get("scope_org_name"),
                scope_workspace_id=r.get("scope_workspace_id"), scope_workspace_name=r.get("scope_workspace_name"),
            )
            for r in rows
        ]

    async def list_group_members_paginated(
        self, connection: asyncpg.Connection, group_id: str, *, limit: int, offset: int
    ) -> tuple[list[GroupMemberRecord], int]:
        """List group members with pagination and scope resolution.

        Args:
            connection: Active asyncpg database connection.
            group_id: UUID of the group.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            Tuple of (members list, total count).
        """
        total_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {SCHEMA}."18_lnk_group_memberships"
            WHERE group_id = $1 AND is_deleted = FALSE AND is_active = TRUE
            """,
            group_id,
        )
        total = total_row["cnt"] if total_row else 0
        rows = await connection.fetch(
            f"""
            SELECT m.id, m.group_id, m.user_id, m.membership_status,
                   m.effective_from, m.effective_to,
                   v.email,
                   dn.property_value AS display_name,
                   m.scope_org_id::text AS scope_org_id,
                   o.name AS scope_org_name,
                   m.scope_workspace_id::text AS scope_workspace_id,
                   w.name AS scope_workspace_name
            FROM {SCHEMA}."18_lnk_group_memberships" m
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = m.user_id
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
                   ON dn.user_id = m.user_id AND dn.property_key = 'display_name'
            LEFT JOIN {SCHEMA}."29_fct_orgs" o ON o.id = m.scope_org_id
            LEFT JOIN {SCHEMA}."34_fct_workspaces" w ON w.id = m.scope_workspace_id
            WHERE m.group_id = $1 AND m.is_deleted = FALSE AND m.is_active = TRUE
            ORDER BY o.name NULLS FIRST, w.name NULLS FIRST, m.effective_from
            LIMIT $2 OFFSET $3
            """,
            group_id, limit, offset,
        )
        members = [
            GroupMemberRecord(
                id=r["id"], group_id=r["group_id"], user_id=r["user_id"],
                membership_status=r["membership_status"],
                effective_from=r["effective_from"], effective_to=r["effective_to"],
                email=r.get("email"), display_name=r.get("display_name"),
                scope_org_id=r.get("scope_org_id"), scope_org_name=r.get("scope_org_name"),
                scope_workspace_id=r.get("scope_workspace_id"), scope_workspace_name=r.get("scope_workspace_name"),
            )
            for r in rows
        ]
        return members, total

    async def list_group_children_paginated(
        self, connection: asyncpg.Connection, group_id: str, *, limit: int, offset: int
    ) -> tuple[list[GroupRecord], int]:
        total_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {SCHEMA}."17_fct_user_groups"
            WHERE parent_group_id = $1 AND is_deleted = FALSE
            """,
            group_id,
        )
        total = total_row["cnt"] if total_row else 0
        rows = await connection.fetch(
            f"""
            SELECT {_SELECT_GROUP_COLS}
            FROM {SCHEMA}."17_fct_user_groups"
            WHERE parent_group_id = $1 AND is_deleted = FALSE
            ORDER BY code
            LIMIT $2 OFFSET $3
            """,
            group_id, limit, offset,
        )
        return [_row_to_group(r) for r in rows], total

    async def count_group_members(
        self, connection: asyncpg.Connection, group_ids: list[str]
    ) -> dict[str, int]:
        """Return {group_id: member_count} for multiple groups in one query."""
        if not group_ids:
            return {}
        rows = await connection.fetch(
            f"""
            SELECT group_id, COUNT(*) as cnt
            FROM {SCHEMA}."18_lnk_group_memberships"
            WHERE group_id = ANY($1) AND is_deleted = FALSE AND is_active = TRUE
            GROUP BY group_id
            """,
            group_ids,
        )
        return {str(r["group_id"]): r["cnt"] for r in rows}

    async def add_member(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        user_id: str,
        created_by: str,
        now: datetime,
    ) -> str:
        membership_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."18_lnk_group_memberships" (
                id, group_id, user_id, membership_status, effective_from, effective_to,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, 'active', $4, NULL,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $5, $6, $7, $8, NULL, NULL)
            """,
            membership_id, group_id, user_id, now, now, now, created_by, created_by,
        )
        return membership_id

    async def remove_member(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        user_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."18_lnk_group_memberships"
            SET is_active = FALSE, is_deleted = TRUE, membership_status = 'removed',
                effective_to = $1, deleted_at = $2, deleted_by = $3,
                updated_at = $4, updated_by = $5
            WHERE group_id = $6 AND user_id = $7 AND is_deleted = FALSE
            """,
            now, now, deleted_by, now, deleted_by, group_id, user_id,
        )
        return result != "UPDATE 0"

    async def list_group_roles(
        self, connection: asyncpg.Connection, group_id: str
    ) -> list[GroupRoleRecord]:
        rows = await connection.fetch(
            f"""
            SELECT gra.id, gra.group_id, gra.role_id, gra.assignment_status,
                   r.code as role_code, r.name as role_name, r.role_level_code
            FROM {SCHEMA}."19_lnk_group_role_assignments" gra
            JOIN {SCHEMA}."16_fct_roles" r ON r.id = gra.role_id
            WHERE gra.group_id = $1 AND gra.is_deleted = FALSE AND gra.is_active = TRUE
            ORDER BY r.role_level_code, r.code
            """,
            group_id,
        )
        return [
            GroupRoleRecord(
                id=r["id"], group_id=r["group_id"], role_id=r["role_id"],
                role_code=r["role_code"], role_name=r["role_name"],
                role_level_code=r["role_level_code"],
                assignment_status=r["assignment_status"],
            )
            for r in rows
        ]

    async def list_group_roles_batch(
        self, connection: asyncpg.Connection, group_ids: list[str]
    ) -> dict[str, list[GroupRoleRecord]]:
        """Batch load roles for multiple groups. Returns {group_id: [roles]}."""
        if not group_ids:
            return {}
        rows = await connection.fetch(
            f"""
            SELECT gra.id, gra.group_id, gra.role_id, gra.assignment_status,
                   r.code as role_code, r.name as role_name, r.role_level_code
            FROM {SCHEMA}."19_lnk_group_role_assignments" gra
            JOIN {SCHEMA}."16_fct_roles" r ON r.id = gra.role_id
            WHERE gra.group_id = ANY($1) AND gra.is_deleted = FALSE AND gra.is_active = TRUE
            ORDER BY r.role_level_code, r.code
            """,
            group_ids,
        )
        result: dict[str, list[GroupRoleRecord]] = {gid: [] for gid in group_ids}
        for r in rows:
            result[r["group_id"]].append(
                GroupRoleRecord(
                    id=r["id"], group_id=r["group_id"], role_id=r["role_id"],
                    role_code=r["role_code"], role_name=r["role_name"],
                    role_level_code=r["role_level_code"],
                    assignment_status=r["assignment_status"],
                )
            )
        return result

    async def assign_role(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        role_id: str,
        created_by: str,
        now: datetime,
    ) -> str:
        assignment_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."19_lnk_group_role_assignments" (
                id, group_id, role_id, assignment_status, effective_from, effective_to,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, 'active', $4, NULL,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $5, $6, $7, $8, NULL, NULL)
            """,
            assignment_id, group_id, role_id, now, now, now, created_by, created_by,
        )
        return assignment_id

    async def revoke_role(
        self,
        connection: asyncpg.Connection,
        *,
        group_id: str,
        role_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."19_lnk_group_role_assignments"
            SET is_active = FALSE, is_deleted = TRUE, assignment_status = 'revoked',
                effective_to = $1, deleted_at = $2, deleted_by = $3,
                updated_at = $4, updated_by = $5
            WHERE group_id = $6 AND role_id = $7 AND is_deleted = FALSE
            """,
            now, now, deleted_by, now, deleted_by, group_id, role_id,
        )
        return result != "UPDATE 0"


def _row_to_group(row: asyncpg.Record) -> GroupRecord:
    return GroupRecord(
        id=str(row["id"]),
        code=row["code"],
        name=row["name"],
        description=row["description"],
        role_level_code=row["role_level_code"],
        tenant_key=row["tenant_key"],
        parent_group_id=str(row["parent_group_id"]) if row["parent_group_id"] else None,
        scope_org_id=str(row["scope_org_id"]) if row["scope_org_id"] else None,
        scope_workspace_id=str(row["scope_workspace_id"]) if row["scope_workspace_id"] else None,
        is_active=row["is_active"],
        is_system=row["is_system"],
        is_locked=row["is_locked"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
