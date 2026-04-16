from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import OrgMemberRecord, OrgRecord, OrgTypeRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="orgs.repository", logger_name="backend.orgs.repository.instrumentation")
class OrgRepository:
    async def list_org_types(self, connection: asyncpg.Connection) -> list[OrgTypeRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description FROM {SCHEMA}."28_dim_org_types" ORDER BY name'
        )
        return [OrgTypeRecord(code=r["code"], name=r["name"], description=r["description"]) for r in rows]

    async def list_orgs(
        self, connection: asyncpg.Connection, *, tenant_key: str
    ) -> list[OrgRecord]:
        """Return all orgs for the tenant (super-admin path)."""
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_type_code, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."29_fct_orgs"
            WHERE tenant_key = $1 AND is_deleted = FALSE
            ORDER BY name
            """,
            tenant_key,
        )
        return [_row_to_org(r) for r in rows]

    async def list_orgs_for_user(
        self, connection: asyncpg.Connection, *, user_id: str, tenant_key: str
    ) -> list[OrgRecord]:
        """Return only orgs the user is an active member of."""
        rows = await connection.fetch(
            f"""
            SELECT o.id, o.tenant_key, o.org_type_code, o.name, o.code AS slug, o.description,
                   o.is_active, o.created_at::text, o.updated_at::text
            FROM {SCHEMA}."29_fct_orgs" o
            JOIN {SCHEMA}."31_lnk_org_memberships" m
              ON m.org_id = o.id AND m.user_id = $1
             AND m.is_active = TRUE AND m.is_deleted = FALSE
            WHERE o.tenant_key = $2 AND o.is_deleted = FALSE
            ORDER BY o.name
            """,
            user_id,
            tenant_key,
        )
        return [_row_to_org(r) for r in rows]

    async def get_org_by_id(
        self, connection: asyncpg.Connection, org_id: str
    ) -> OrgRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_type_code, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."29_fct_orgs"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            org_id,
        )
        return _row_to_org(row) if row else None

    async def get_org_by_name(
        self, connection: asyncpg.Connection, name: str, tenant_key: str
    ) -> OrgRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_type_code, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."29_fct_orgs"
            WHERE LOWER(name) = LOWER($1) AND tenant_key = $2 AND is_deleted = FALSE
            """,
            name,
            tenant_key,
        )
        return _row_to_org(row) if row else None

    async def get_org_by_slug(
        self, connection: asyncpg.Connection, slug: str, tenant_key: str
    ) -> OrgRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_type_code, name, code AS slug, description,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."29_fct_orgs"
            WHERE code = $1 AND tenant_key = $2 AND is_deleted = FALSE
            """,
            slug,
            tenant_key,
        )
        return _row_to_org(row) if row else None

    async def create_org(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        tenant_key: str,
        org_type_code: str,
        name: str,
        slug: str,
        description: str | None,
        created_by: str,
        now: datetime,
    ) -> OrgRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."29_fct_orgs"
                (
                    id, tenant_key, org_type_code, code, name, description,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
            VALUES (
                $1, $2, $3, $4, $5, $6,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $7, $8, $9, $10, NULL, NULL
            )
            RETURNING id, tenant_key, org_type_code, name, code AS slug, description,
                      is_active, created_at::text, updated_at::text
            """,
            org_id,
            tenant_key,
            org_type_code,
            slug,
            name,
            description or "",
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_org(row)

    async def update_org(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_disabled: bool | None = None,
        updated_by: str,
        now: datetime,
    ) -> OrgRecord | None:
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
        if is_disabled is not None:
            fields.append(f"is_active = ${idx}")
            values.append(not is_disabled)
            idx += 1

        if not fields:
            return await self.get_org_by_id(connection, org_id)

        values.append(org_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."29_fct_orgs"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, tenant_key, org_type_code, name, code AS slug, description,
                      is_active, created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_org(row) if row else None

    async def list_org_members(
        self, connection: asyncpg.Connection, org_id: str
    ) -> list[OrgMemberRecord]:
        rows = await connection.fetch(
            f"""
            SELECT m.id, m.org_id, m.user_id, m.membership_type AS role, m.is_active,
                   m.effective_from::text AS joined_at,
                   v.email,
                   dn.property_value AS display_name
            FROM {SCHEMA}."31_lnk_org_memberships" m
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = m.user_id
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn ON dn.user_id = m.user_id AND dn.property_key = 'display_name'
            WHERE m.org_id = $1 AND m.is_active = TRUE AND m.is_deleted = FALSE
            ORDER BY m.effective_from
            """,
            org_id,
        )
        return [_row_to_member(r) for r in rows]

    async def add_org_member(
        self,
        connection: asyncpg.Connection,
        *,
        membership_id: str,
        org_id: str,
        user_id: str,
        role: str,
        created_by: str,
        now: datetime,
    ) -> OrgMemberRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."31_lnk_org_memberships" (
                id, org_id, user_id, membership_type, membership_status,
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
            ON CONFLICT (org_id, user_id) WHERE is_deleted = FALSE
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
            RETURNING id, org_id, user_id, membership_type AS role, is_active, effective_from::text AS joined_at
            """,
            membership_id,
            org_id,
            user_id,
            role,
            now,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_member(row)

    async def remove_org_member(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        user_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."31_lnk_org_memberships"
            SET
                is_active = FALSE,
                is_deleted = TRUE,
                membership_status = 'removed',
                effective_to = $1,
                updated_at = $2,
                updated_by = $3,
                deleted_at = $4,
                deleted_by = $5
            WHERE org_id = $6 AND user_id = $7 AND is_deleted = FALSE
            """,
            now,
            now,
            deleted_by,
            now,
            deleted_by,
            org_id,
            user_id,
        )
        return result != "UPDATE 0"

    async def update_org_member_role(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        user_id: str,
        role: str,
        updated_by: str,
        now: datetime,
    ) -> OrgMemberRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."31_lnk_org_memberships"
            SET membership_type = $1, updated_at = $2, updated_by = $3
            WHERE org_id = $4 AND user_id = $5 AND is_deleted = FALSE
            RETURNING id, org_id, user_id, membership_type AS role, is_active, effective_from::text AS joined_at
            """,
            role,
            now,
            updated_by,
            org_id,
            user_id,
        )
        if row is None:
            return None
        # Fetch email / display_name separately (same pattern as list_org_members)
        extra = await connection.fetchrow(
            f"""
            SELECT v.email, dn.property_value AS display_name
            FROM {SCHEMA}."42_vw_auth_users" v
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" dn
              ON dn.user_id = v.user_id AND dn.property_key = 'display_name'
            WHERE v.user_id = $1
            """,
            user_id,
        )
        return OrgMemberRecord(
            id=row["id"],
            org_id=row["org_id"],
            user_id=row["user_id"],
            role=row["role"],
            is_active=row["is_active"],
            joined_at=row["joined_at"],
            email=extra["email"] if extra else None,
            display_name=extra["display_name"] if extra else None,
        )


def _row_to_org(r) -> OrgRecord:
    return OrgRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_type_code=r["org_type_code"],
        name=r["name"],
        slug=r["slug"],
        description=r["description"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_member(r) -> OrgMemberRecord:
    return OrgMemberRecord(
        id=r["id"],
        org_id=r["org_id"],
        user_id=r["user_id"],
        role=r["role"],
        is_active=r["is_active"],
        joined_at=r["joined_at"],
        email=r.get("email"),
        display_name=r.get("display_name"),
    )
