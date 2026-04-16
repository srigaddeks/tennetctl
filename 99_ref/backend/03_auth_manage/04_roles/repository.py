from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import uuid4

import asyncpg

from .models import RoleLevelRecord, RolePermissionLinkRecord, RoleRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="roles.repository", logger_name="backend.roles.repository.instrumentation")
class RoleRepository:
    async def list_role_levels(self, connection: asyncpg.Connection) -> list[RoleLevelRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, name, description, sort_order
            FROM {SCHEMA}."13_dim_role_levels"
            ORDER BY sort_order
            """
        )
        return [
            RoleLevelRecord(id=r["id"], code=r["code"], name=r["name"],
                            description=r["description"], sort_order=r["sort_order"])
            for r in rows
        ]

    async def list_roles(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope_org_id: str | None = None,
    ) -> list[RoleRecord]:
        if scope_org_id is not None:
            rows = await connection.fetch(
                f"""
                SELECT id, code, name, description, role_level_code, tenant_key,
                       scope_org_id, scope_workspace_id,
                       is_active, is_disabled, is_system, created_at, updated_at
                FROM {SCHEMA}."16_fct_roles"
                WHERE is_deleted = FALSE
                  AND role_level_code IN ('org', 'workspace')
                  AND (
                      (
                          (tenant_key = $1 OR tenant_key = '__platform__')
                          AND scope_org_id IS NULL
                          AND scope_workspace_id IS NULL
                      )
                      OR scope_org_id = $2
                  )
                ORDER BY role_level_code, code
                """,
                tenant_key,
                scope_org_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT id, code, name, description, role_level_code, tenant_key,
                       scope_org_id, scope_workspace_id,
                       is_active, is_disabled, is_system, created_at, updated_at
                FROM {SCHEMA}."16_fct_roles"
                WHERE (tenant_key = $1 OR tenant_key = '__platform__') AND is_deleted = FALSE
                ORDER BY role_level_code, code
                """,
                tenant_key,
            )
        return [_row_to_role(r) for r in rows]

    async def get_role_by_id(
        self, connection: asyncpg.Connection, role_id: str
    ) -> RoleRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, description, role_level_code, tenant_key,
                   scope_org_id, scope_workspace_id,
                   is_active, is_disabled, is_system, created_at, updated_at
            FROM {SCHEMA}."16_fct_roles"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            role_id,
        )
        return _row_to_role(row) if row else None

    async def create_role(
        self,
        connection: asyncpg.Connection,
        *,
        code: str,
        name: str,
        description: str,
        role_level_code: str,
        tenant_key: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        created_by: str,
        now: datetime,
    ) -> RoleRecord:
        role_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."16_fct_roles" (
                id, tenant_key, role_level_code, code, name, description,
                scope_org_id, scope_workspace_id,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $9, $10, $11, $12, NULL, NULL)
            """,
            role_id, tenant_key, role_level_code, code, name, description,
            scope_org_id, scope_workspace_id,
            now, now, created_by, created_by,
        )
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, description, role_level_code, tenant_key,
                   scope_org_id, scope_workspace_id,
                   is_active, is_disabled, is_system, created_at, updated_at
            FROM {SCHEMA}."16_fct_roles" WHERE id = $1
            """,
            role_id,
        )
        return _row_to_role(row)  # type: ignore[arg-type]

    async def update_role(
        self,
        connection: asyncpg.Connection,
        *,
        role_id: str,
        name: str | None,
        description: str | None,
        is_disabled: bool | None,
        updated_by: str,
        now: datetime,
    ) -> RoleRecord | None:
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
        if is_disabled is not None:
            _add("is_disabled", is_disabled)
            if is_disabled:
                _add("is_active", False)
            else:
                _add("is_active", True)

        params.append(role_id)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."16_fct_roles"
            SET {", ".join(sets)}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, code, name, description, role_level_code, tenant_key,
                      scope_org_id, scope_workspace_id,
                      is_active, is_disabled, is_system, created_at, updated_at
            """,
            *params,
        )
        return _row_to_role(row) if row else None

    async def delete_role(
        self,
        connection: asyncpg.Connection,
        *,
        role_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."16_fct_roles"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE AND is_system = FALSE
            """,
            now, deleted_by, now, deleted_by, role_id,
        )
        return result != "UPDATE 0"

    async def assign_permission(
        self,
        connection: asyncpg.Connection,
        *,
        role_id: str,
        feature_permission_id: str,
        created_by: str,
        now: datetime,
    ) -> str:
        existing = await connection.fetchrow(
            f"""
            SELECT id, is_deleted, is_active
            FROM {SCHEMA}."20_lnk_role_feature_permissions"
            WHERE role_id = $1 AND feature_permission_id = $2
            """,
            role_id, feature_permission_id,
        )

        if existing:
            if not existing["is_deleted"] and existing["is_active"]:
                raise asyncpg.UniqueViolationError("Permission is already assigned to this role.")

            await connection.execute(
                f"""
                UPDATE {SCHEMA}."20_lnk_role_feature_permissions"
                SET is_active = TRUE,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    deleted_by = NULL,
                    updated_at = $1,
                    updated_by = $2
                WHERE id = $3
                """,
                now, created_by, existing["id"],
            )
            return existing["id"]

        link_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_lnk_role_feature_permissions" (
                id, role_id, feature_permission_id,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $4, $5, $6, $7, NULL, NULL)
            """,
            link_id, role_id, feature_permission_id, now, now, created_by, created_by,
        )
        return link_id

    async def revoke_permission(
        self,
        connection: asyncpg.Connection,
        *,
        role_id: str,
        feature_permission_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_lnk_role_feature_permissions"
            SET is_active = FALSE, is_deleted = TRUE, deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE role_id = $5 AND feature_permission_id = $6 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, role_id, feature_permission_id,
        )
        return result != "UPDATE 0"

    async def list_role_permissions(
        self, connection: asyncpg.Connection, role_id: str
    ) -> list[RolePermissionLinkRecord]:
        rows = await connection.fetch(
            f"""
            SELECT rfp.id, rfp.role_id, rfp.feature_permission_id,
                   fp.code as fp_code, fp.feature_flag_code, fp.permission_action_code, fp.name as fp_name
            FROM {SCHEMA}."20_lnk_role_feature_permissions" rfp
            JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
            WHERE rfp.role_id = $1 AND rfp.is_deleted = FALSE AND rfp.is_active = TRUE
            ORDER BY fp.feature_flag_code, fp.permission_action_code
            """,
            role_id,
        )
        return [
            RolePermissionLinkRecord(
                id=r["id"], role_id=r["role_id"],
                feature_permission_id=r["feature_permission_id"],
                feature_permission_code=r["fp_code"],
                feature_flag_code=r["feature_flag_code"],
                permission_action_code=r["permission_action_code"],
                permission_name=r["fp_name"],
            )
            for r in rows
        ]


    async def list_role_permissions_batch(
        self, connection: asyncpg.Connection, role_ids: list[str]
    ) -> dict[str, list[RolePermissionLinkRecord]]:
        """Batch load permissions for multiple roles. Returns {role_id: [permissions]}."""
        if not role_ids:
            return {}
        rows = await connection.fetch(
            f"""
            SELECT rfp.id, rfp.role_id, rfp.feature_permission_id,
                   fp.code as fp_code, fp.feature_flag_code, fp.permission_action_code, fp.name as fp_name
            FROM {SCHEMA}."20_lnk_role_feature_permissions" rfp
            JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
            WHERE rfp.role_id = ANY($1) AND rfp.is_deleted = FALSE AND rfp.is_active = TRUE
            ORDER BY fp.feature_flag_code, fp.permission_action_code
            """,
            role_ids,
        )
        result: dict[str, list[RolePermissionLinkRecord]] = {rid: [] for rid in role_ids}
        for r in rows:
            result[r["role_id"]].append(
                RolePermissionLinkRecord(
                    id=r["id"], role_id=r["role_id"],
                    feature_permission_id=r["feature_permission_id"],
                    feature_permission_code=r["fp_code"],
                    feature_flag_code=r["feature_flag_code"],
                    permission_action_code=r["permission_action_code"],
                    permission_name=r["fp_name"],
                )
            )
        return result

    async def list_groups_using_role(
        self,
        connection: asyncpg.Connection,
        role_id: str,
        *,
        scope_org_id: str | None = None,
    ) -> list[dict]:
        if scope_org_id is not None:
            rows = await connection.fetch(
                f"""
                SELECT g.id, g.code, g.name, g.role_level_code, g.is_system, g.is_active,
                       (SELECT COUNT(*) FROM {SCHEMA}."18_lnk_group_memberships" m
                        WHERE m.group_id = g.id AND m.is_deleted = FALSE AND m.is_active = TRUE) as member_count
                FROM {SCHEMA}."19_lnk_group_role_assignments" gra
                JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gra.group_id
                WHERE gra.role_id = $1
                  AND gra.is_deleted = FALSE
                  AND gra.is_active = TRUE
                  AND g.is_deleted = FALSE
                  AND g.scope_org_id = $2
                ORDER BY g.role_level_code, g.name
                """,
                role_id,
                scope_org_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT g.id, g.code, g.name, g.role_level_code, g.is_system, g.is_active,
                       (SELECT COUNT(*) FROM {SCHEMA}."18_lnk_group_memberships" m
                        WHERE m.group_id = g.id AND m.is_deleted = FALSE AND m.is_active = TRUE) as member_count
                FROM {SCHEMA}."19_lnk_group_role_assignments" gra
                JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gra.group_id
                WHERE gra.role_id = $1 AND gra.is_deleted = FALSE AND gra.is_active = TRUE
                  AND g.is_deleted = FALSE
                ORDER BY g.role_level_code, g.name
                """,
                role_id,
            )
        return [dict(r) for r in rows]


def _row_to_role(row: asyncpg.Record) -> RoleRecord:
    return RoleRecord(
        id=row["id"], code=row["code"], name=row["name"],
        description=row["description"], role_level_code=row["role_level_code"],
        tenant_key=row["tenant_key"],
        scope_org_id=row["scope_org_id"] if row["scope_org_id"] else None,
        scope_workspace_id=row["scope_workspace_id"] if row["scope_workspace_id"] else None,
        is_active=row["is_active"],
        is_disabled=row["is_disabled"], is_system=row["is_system"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
